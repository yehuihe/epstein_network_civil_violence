import nest_asyncio

nest_asyncio.apply()
# add new features and mechanisms to collect data for plot
import mesa
import numpy as np

from epstein_civil_violence.model import EpsteinCivilViolence
from mean_field_civil_violence.agent import Inhabitant
from mean_field_civil_violence.agent import Police


class EpsteinNetworkCivilViolence(EpsteinCivilViolence):
    """
    Extended model from
    Model 1 from "Modeling civil violence: An agent-based computational
    approach," by Joshua Epstein.
    http://www.pnas.org/content/99/suppl_3/7243.full
    Attributes:
        height: grid height
        width: grid width
        citizen_density: approximate % of cells occupied by citizens.
        cop_density: approximate % of cells occupied by cops.
        citizen_vision: number of cells in each direction (N, S, E and W) that
            citizen can inspect
        cop_vision: number of cells in each direction (N, S, E and W) that cop
            can inspect
        legitimacy:  (L) citizens' perception of regime legitimacy, equal
            across all citizens
        max_jail_term: (J_max)
        active_threshold: if (grievance - (risk_aversion * arrest_probability))
            > threshold, citizen rebels
        arrest_prob_constant: set to ensure agents make plausible arrest
            probability estimates
        movement: binary, whether agents try to move at step end
        max_iters: model may not have a natural stopping point, so we set a
            max.
        alpha: Deterrent effect.
        rumor_effect: Network rumor effect posed by active agents.
    """

    def __init__(
            self,
            width=40,
            height=40,
            citizen_density=0.7,
            cop_density=0.074,
            citizen_vision=7,
            cop_vision=7,
            legitimacy=0.8,
            max_jail_term=1000,
            active_threshold=0.1,
            arrest_prob_constant=2.3,
            movement=True,
            max_iters=1000,
            alpha=0.1,
            jail_factor=1.1,
            # impact_chance=0.5,
            legitimacy_impact=0.2,
            # incitation_threshold=10,
            legitimacy_type="basic",  # "basic", "heterogeneous", "by_regions"
            legitimacy_matrix=None,
            use_mean_field=True,
            legitimacy_width=0.1,
            cop_density_mode='constant',  # Parameter to select the change mode of cop density (constant, gradual)
            legitimacy_mode='constant'  # Parameter to select the change mode of legitimacy (constant, gradual, drop)

    ):
        super().__init__(
            width,
            height,
            citizen_density,
            cop_density,
            citizen_vision,
            cop_vision,
            legitimacy,
            max_jail_term,
            active_threshold,
            arrest_prob_constant,
            movement,
            max_iters,
        )
        self.iteration = 0
        self.schedule = mesa.time.RandomActivation(self)
        # self.grid = mesa.space.MultiGrid(width, height, torus=True)
        self.grid = mesa.space.SingleGrid(width, height, torus=True)
        self.alpha = alpha
        self.jail_factor = jail_factor
        self.legitimacy_impact = legitimacy_impact
        self.cop_density_mode = cop_density_mode  # Store the cop density change mode
        self.legitimacy_mode = legitimacy_mode  # Store the legitimacy change mode
        self.active_outburst = False  # Indicates if an outburst is currently happening
        self.last_outburst_ended = 0  # Time the last outburst ended
        self.waiting_times = []  # List to store waiting times
        self.outburst_sizes = []  # Store the size of each outburst
        self.current_outburst_size = 0  # Track the size of the current outburst
        self.total_citizen = 0

        if use_mean_field == 1:
            use_mean_field = True
        if use_mean_field == 0:
            use_mean_field = False

        model_reporters = {
            "Quiescent": lambda m: self.count_type_citizens(m, "Quiescent"),
            "Active": lambda m: self.count_type_citizens(m, "Active"),
            "Jailed": self.count_jailed,
            "Cops": self.count_cops,
            "Waiting_Times": lambda m: self.waiting_times,
            "Legitimacy": lambda m: self.legitimacy,
            "Cop_Density": lambda m: self.cop_density,
            "Stable Agents": lambda m: self.count_stable_agents(),
            "Active_Ratio": lambda m: self.count_type_citizens(m, "Active") / self.total_citizen
        }
        agent_reporters = {
            "x": lambda a: a.pos[0],
            "y": lambda a: a.pos[1],
            "breed": lambda a: a.breed,
            "jail_sentence": lambda a: getattr(a, "jail_sentence", None),
            "condition": lambda a: getattr(a, "condition", None),
            "arrest_probability": lambda a: getattr(a, "arrest_probability", None),
            "regime_legitimacy": lambda a: getattr(a, "regime_legitimacy", None),
        }
        self.datacollector = mesa.DataCollector(
            model_reporters=model_reporters, agent_reporters=agent_reporters
        )
        unique_id = 0
        if self.cop_density + self.citizen_density > 1:
            raise ValueError("Cop density + citizen density must be less than 1")

        # Calculate the size of each region based on the legitimacy matrix
        if legitimacy_matrix is not None:
            region_height = height / legitimacy_matrix.shape[0]
            region_width = width / legitimacy_matrix.shape[1]

        for contents, (x, y) in self.grid.coord_iter():
            if self.random.random() < self.cop_density:
                cop = Police(unique_id, self, (x, y), vision=self.cop_vision)
                unique_id += 1
                self.grid[x][y] = cop
                self.schedule.add(cop)
            elif self.random.random() < (self.cop_density + self.citizen_density):
                # Initialize legitimacy
                regime_legitimacy = self.legitimacy
                average_legitimacy = self.legitimacy

                if legitimacy_type == "heterogeneous":
                    regime_legitimacy = np.random.uniform(max(0, regime_legitimacy - legitimacy_width),
                                                          min(1, regime_legitimacy + legitimacy_width))
                elif legitimacy_type == "by_regions" and legitimacy_matrix is not None:
                    region_x = int(x // region_width)
                    region_y = int(y // region_height)
                    regime_legitimacy = legitimacy_matrix[region_y, region_x]
                    average_legitimacy = np.mean(legitimacy_matrix)

                citizen = Inhabitant(
                    unique_id,
                    self,
                    (x, y),
                    hardship=self.random.random(),
                    regime_legitimacy=regime_legitimacy,
                    risk_aversion=self.random.random(),
                    threshold=self.active_threshold,
                    vision=self.citizen_vision,
                    alpha=self.alpha,
                    jail_factor=self.jail_factor,
                    legitimacy_impact=self.legitimacy_impact,
                    use_mean_field=use_mean_field,
                    average_legitimacy = average_legitimacy,
                    legitimacy_width=legitimacy_width
                )
                unique_id += 1
                self.grid[x][y] = citizen
                self.schedule.add(citizen)
                self.total_citizen += 1

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        active_count = self.count_type_citizens(self, "Active")
        if self.iteration == 300 and self.legitimacy_mode == 'drop':
            self.legitimacy = max(0, self.legitimacy - 0.3)
        elif self.legitimacy_mode == 'gradual':
            self.legitimacy = max(0, self.legitimacy - 0.001)
        if self.cop_density_mode == 'gradual':
            self.cop_density = max(0, self.cop_density - 0.00005)

        if active_count >= 100 and not self.active_outburst:
            if self.last_outburst_ended != 0:
                wait_time = self.schedule.steps - self.last_outburst_ended
                self.waiting_times.append(wait_time)
            self.active_outburst = True
        if active_count < 100 and self.active_outburst:
            self.last_outburst_ended = self.schedule.steps
            self.active_outburst = False

        if active_count >= 100:
            self.current_outburst_size += active_count
        else:
            if self.current_outburst_size > 0:
                self.outburst_sizes.append(self.current_outburst_size)
                self.current_outburst_size = 0

        self.schedule.step()
        self.datacollector.collect(self)
        self.iteration += 1
        if self.iteration > self.max_iters:
            self.running = False

    def count_stable_agents(self):
        stable_agents = [agent for agent in self.schedule.agents if isinstance(agent, Inhabitant) and agent.is_stable]
        return len(stable_agents)