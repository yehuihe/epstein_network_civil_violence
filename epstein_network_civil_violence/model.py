import nest_asyncio

nest_asyncio.apply()
# add new features and mechanisms to collect data for plot
import mesa

from epstein_civil_violence.model import EpsteinCivilViolence
from epstein_network_civil_violence.agent import Inhabitant
from epstein_network_civil_violence.agent import Police

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
            impact_chance=0.5,
            legitimacy_impact=0.2,
            incitation_threshold=10,
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
        self.grid = mesa.space.SingleGrid(width, height, torus=True)
        self.alpha = alpha
        self.jail_factor = jail_factor
        self.impact_chance = impact_chance
        self.legitimacy_impact = legitimacy_impact
        self.incitation_threshold = incitation_threshold
        self.cop_density_mode = cop_density_mode  # Store the cop density change mode
        self.legitimacy_mode = legitimacy_mode  # Store the legitimacy change mode
        self.active_outburst = False  # Indicates if an outburst is currently happening
        self.last_outburst_ended = 0  # Time the last outburst ended
        self.waiting_times = []  # List to store waiting times
        self.outburst_sizes = []  # Store the size of each outburst
        self.current_outburst_size = 0  # Track the size of the current outburst

        model_reporters = {
            "Quiescent": lambda m: self.count_type_citizens(m, "Quiescent"),
            "Active": lambda m: self.count_type_citizens(m, "Active"),
            "Jailed": self.count_jailed,
            "Cops": self.count_cops,
            "Waiting_Times": lambda m: self.waiting_times,
            "Legitimacy": lambda m: self.legitimacy,
            "Cop_Density": lambda m: self.cop_density

        }
        agent_reporters = {
            "x": lambda a: a.pos[0],
            "y": lambda a: a.pos[1],
            "breed": lambda a: a.breed,
            "jail_sentence": lambda a: getattr(a, "jail_sentence", None),
            "condition": lambda a: getattr(a, "condition", None),
            "arrest_probability": lambda a: getattr(a, "arrest_probability", None),
        }
        self.datacollector = mesa.DataCollector(
            model_reporters=model_reporters, agent_reporters=agent_reporters
        )
        unique_id = 0
        if self.cop_density + self.citizen_density > 1:
            raise ValueError("Cop density + citizen density must be less than 1")
        for contents, (x, y) in self.grid.coord_iter():
            if self.random.random() < self.cop_density:
                cop = Police(unique_id, self, (x, y), vision=self.cop_vision)
                unique_id += 1
                self.grid[x][y] = cop
                self.schedule.add(cop)
            elif self.random.random() < (self.cop_density + self.citizen_density):
                if (0 <= x < 50) and (0 <= y < 50):
                    personal_regime_legitimacy = 0
                else:
                    personal_regime_legitimacy = self.random.random()
                citizen = Inhabitant(
                    unique_id,
                    self,
                    (x, y),
                    hardship=self.random.random(),
                    regime_legitimacy = personal_regime_legitimacy,
                    risk_aversion=self.random.random(),
                    threshold=self.active_threshold,
                    vision=self.citizen_vision,
                    alpha=self.alpha,
                    jail_factor=self.jail_factor,
                    impact_chance = self.impact_chance,
                    legitimacy_impact=self.legitimacy_impact,
                    incitation_threshold=self.incitation_threshold,
                )
                unique_id += 1
                self.grid[x][y] = citizen
                self.schedule.add(citizen)

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        active_count = self.count_type_citizens(self,
                                                "Active")  # Define and calculate the current number of active citizens
        # print(f"Active Count: {active_count}")

        if self.iteration == 300 and self.legitimacy_mode == 'drop':
            self.legitimacy = max(0, self.legitimacy - 0.3)
        elif self.legitimacy_mode == 'gradual':
            self.legitimacy = max(0, self.legitimacy - 0.001)
        if self.cop_density_mode == 'gradual':
            self.cop_density = max(0, self.cop_density - 0.00005)  # Gradually decrease cop density, but not below 0

        if active_count >= 100 and not self.active_outburst:
            if self.last_outburst_ended != 0:  # Not the first outburst
                wait_time = self.schedule.steps - self.last_outburst_ended
                self.waiting_times.append(wait_time)
                print(f"Outburst starts, wait time recorded: {wait_time}")  # Debug output
            self.active_outburst = True
        if active_count < 100 and self.active_outburst:
            self.last_outburst_ended = self.schedule.steps
            self.active_outburst = False
            print(f"Outburst ends at step {self.last_outburst_ended}")  # Debug output

        if active_count >= 100:
            self.current_outburst_size += active_count  # Accumulate the size of the current outburst
        else:
            if self.current_outburst_size > 0:  # An outburst has just ended
                self.outburst_sizes.append(self.current_outburst_size)
                self.current_outburst_size = 0  # Reset for the next outburst

        self.schedule.step()
        self.datacollector.collect(self)
        self.iteration += 1
        if self.iteration > self.max_iters:
            self.running = False
