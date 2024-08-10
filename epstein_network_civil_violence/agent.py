import math
import numpy as np

from epstein_civil_violence.agent import Citizen, Cop


class Inhabitant(Citizen):

    def __init__(

            self,
            unique_id,
            model,
            pos,
            hardship,
            regime_legitimacy,
            risk_aversion,
            threshold,
            vision,
            alpha,
            jail_factor,
            # impact_chance,
            legitimacy_impact,
            use_mean_field,
            average_legitimacy,
            legitimacy_width=0.1
    ):
        """
        Create a new Inhabitant.
        Args:
            unique_id: unique int
            x, y: Grid coordinates
            hardship: Agent's 'perceived hardship (i.e., physical or economic
                privation).' Exogenous, drawn from U(0,1).
            regime_legitimacy: Agent's perception of regime legitimacy, equal
                across agents.  Exogenous.
            risk_aversion: Exogenous, drawn from U(0,1).
            threshold: if (grievance - (risk_aversion * arrest_probability)) >
                threshold, go/remain Active
            vision: number of cells in each direction (N, S, E and W) that
                agent can inspect. Exogenous.
            model: model instance
            alpha: Deterrent effect.
            jail_factor: grievance modifier that agents leave jail.
            legitimacy_impact: strength of legitimacy impact by incitation.
        """

        super().__init__(
            unique_id,
            model,
            pos,
            hardship,
            regime_legitimacy,
            risk_aversion,
            threshold,
            vision)
        self.breed = "citizen"
        self.condition = "Quiescent"
        self.jail_sentence = 0
        self.grievance = self.hardship * (1 - self.regime_legitimacy)
        self.arrest_probability = None
        self.alpha = alpha
        self.jail_factor = jail_factor
        # self.impact_chance = impact_chance
        self.legitimacy_impact = legitimacy_impact
        self.incitation_num = 0
        # self.incitation_threshold = incitation_threshold
        self.use_mean_field = use_mean_field

        self.cops_in_vision = 0
        self.actives_in_vision = 0
        self.empty_neighbors = None

        # might not use
        if self.random.random() < 0.2:
            self.ideology_not_change = True
        else:
            self.ideology_not_change = False

        # stable state
        self.average_legitimacy = average_legitimacy
        self.legitimacy_stability_threshold = 0.005
        self.is_stable = False
    '''
    def update_neighbors(self):
        self.neighborhood = list(self.model.grid.get_neighborhood(self.pos, moore=True, radius=self.vision))
        self.neighbors = self.model.grid.get_cell_list_contents(self.neighborhood)
        self.empty_neighbors = [c for c in self.neighborhood if self.model.grid.is_cell_empty(c)]

    def update_next_neighbors(self):
        next_neighbors = list(self.model.grid.get_neighbors(self.pos, moore=True, radius=1))
        self.closed_neighbors = [neighbor for neighbor in next_neighbors if neighbor.breed == "citizen"]
    '''

    def update_next_neighbors(self):
        next_neighbors = self.model.grid.get_neighbors(
            self.pos, moore=True, radius=1
        )

        self.closed_neighbors = [neighbor for neighbor in next_neighbors
                              if neighbor.breed == "citizen"]

    def update_estimated_arrest_probability(self):
        """
        Based on the ratio of cops to actives in my neighborhood, estimate the
        p(Arrest | I go active).
        """
        cops_in_vision = len([c for c in self.neighbors if c.breed == "cop"])
        actives_in_vision = 1.0  # citizen counts herself
        for c in self.neighbors:
            if (
                    c.breed == "citizen"
                    and c.condition == "Active"
                    and c.jail_sentence == 0
            ):
                actives_in_vision += 1
        self.arrest_probability = 1 - math.exp(
            -1 * self.model.arrest_prob_constant * (cops_in_vision / actives_in_vision)
        )
        self.cops_in_vision = cops_in_vision
        self.actives_in_vision = actives_in_vision

    def step(self):
        """
        Decide whether to activate, then move if applicable.
        """

        if self.jail_sentence:
            self.jail_sentence -= 1
            if self.jail_sentence == 0:
                self.update_regime_legitimacy_leave_jail()
            return  # no other changes or movements if agent is in jail.


        # Calculate the legitimacy change
        legitimacy_difference = abs(self.regime_legitimacy - self.average_legitimacy)
        self.is_stable = legitimacy_difference < self.legitimacy_stability_threshold

        self.update_neighbors()
        self.update_next_neighbors()
        self.update_estimated_arrest_probability()

        if self.use_mean_field:
            self.mean_field_spread()

        self.grievance = self.hardship * (1 - self.regime_legitimacy)

        net_risk = self.risk_aversion * self.arrest_probability * self.random.randint(0,
                                                                                      self.model.max_jail_term) ** self.alpha
        if self.grievance - net_risk > self.threshold:
            self.condition = "Active"
        else:
            self.condition = "Quiescent"
        if self.model.movement and self.empty_neighbors:
            new_pos = self.random.choice(self.empty_neighbors)
            self.model.grid.move_agent(self, new_pos)

        # net_risk = self.risk_aversion * self.arrest_probability * self.random.randint(0,
        #                                                                               self.model.max_jail_term) ** self.alpha - 0.3
        #
        # if self.condition == "Quiescent":
        #     if self.grievance - net_risk > self.threshold and self.actives_in_vision >= (2 * self.cops_in_vision):
        #         self.condition = "Active"
        #     else:
        #         self.condition = "Quiescent"
        # else:
        #     if self.grievance - net_risk < self.threshold or self.cops_in_vision >= 1:
        #         self.condition = "Quiescent"
        #
        # # making arrest if incitation number greater than threshold
        # if self.incitation_num > self.incitation_threshold:
        #     sentence = self.random.randint(0, self.model.max_jail_term)
        #     self.jail_sentence = sentence
        #     self.condition = "Quiescent"
        #     self.incitation_num = 0



        if self.model.movement and self.empty_neighbors:
            new_pos = self.random.choice(self.empty_neighbors)
            self.model.grid.move_agent(self, new_pos)


    def update_regime_legitimacy_leave_jail(self):
        self.regime_legitimacy *= self.jail_factor
        self.regime_legitimacy = max(0, min(self.regime_legitimacy, 1))

    def mean_field_spread(self):
        # if self.ideology_not_change:
        #     return
        if not self.closed_neighbors:
            return

        # Calculate the average regime_legitimacy of the surrounding neighbors
        total_legitimacy = sum(neighbor.regime_legitimacy for neighbor in self.closed_neighbors)+self.regime_legitimacy
        mean_legitimacy = total_legitimacy / (len(self.closed_neighbors)+1)

        # Adjust its own regime_legitimacy based on the average regime_legitimacy and its own legitimacy_impact
        self.regime_legitimacy += self.legitimacy_impact * (mean_legitimacy - self.regime_legitimacy)

        # Ensure that regime_legitimacy is between 0 and 1
        self.regime_legitimacy = max(0, min(1, self.regime_legitimacy))

class Police(Cop):
    def __init__(self, unique_id, model, pos, vision):
        """
        Create a new Cop.
        Args:
            unique_id: unique int
            x, y: Grid coordinates
            vision: number of cells in each direction (N, S, E and W) that
                agent can inspect. Exogenous.
            model: model instance
        """
        super().__init__(unique_id, model, pos, vision)
        self.breed = "cop"
        # self.pos = pos
        # self.vision = vision

    def step(self):
        """
        Inspect local vision and arrest a random active agent. Move if
        applicable.
        """
        self.update_neighbors()
        active_neighbors = []
        for agent in self.neighbors:
            if (
                    agent.breed == "citizen"
                    and agent.condition == "Active"
                    and agent.jail_sentence == 0
            ):
                active_neighbors.append(agent)
        if active_neighbors:
            arrestee = self.random.choice(active_neighbors)
            if self.random.random() < arrestee.arrest_probability:
                sentence = self.random.randint(0, self.model.max_jail_term)
                arrestee.jail_sentence = sentence
                arrestee.condition = "Quiescent"
                
            # Get Moore neighborhood of the arrestee
            arrestee_neighborhood = self.model.grid.get_neighborhood(arrestee.pos, moore=True, radius=1)
            arrestee_empty_neighbors = [pos for pos in arrestee_neighborhood if self.model.grid.is_cell_empty(pos)]
            # Filter to ensure the position is within the cop's vision
            arrestee_empty_neighbors_in_vision = [pos for pos in arrestee_empty_neighbors if pos in self.neighborhood]
            
            if arrestee_empty_neighbors_in_vision:
                new_pos = self.random.choice(arrestee_empty_neighbors_in_vision)
            else:
                new_pos = self.random.choice(self.empty_neighbors)
        else:
            if self.model.movement and self.empty_neighbors:
                new_pos = self.random.choice(self.empty_neighbors)
                self.model.grid.move_agent(self, new_pos)



'''
from mesa.space import SingleGrid
class MultiAgentGrid(SingleGrid):
    def __init__(self, width, height, torus=False):
        super().__init__(width, height, torus)
        self._grid = {}  # 使用字典来存储代理
        for x in range(width):
            for y in range(height):
                self._grid[(x, y)] = set()

    def place_agent(self, agent, pos):
        """
        Place an agent at the given position, adding to any agents already
        in that position.
        """
        if self.out_of_bounds(pos):
            raise Exception("Position out of bounds")
        if pos not in self._grid:
            self._grid[pos] = set()
        self._grid[pos].add(agent)
        agent.pos = pos

    def remove_agent(self, agent):
        """
        Remove an agent from the grid.
        """
        if agent.pos in self._grid and agent in self._grid[agent.pos]:
            self._grid[agent.pos].remove(agent)
            if len(self._grid[agent.pos]) == 0:
                del self._grid[agent.pos]
            agent.pos = None
            
    def move_agent(self, agent, pos):
        """
        Move an agent to a new position, allowing multiple agents in the same position.
        """
        self.remove_agent(agent)
        self.place_agent(agent, pos)
    
    def coord_iter(self):
        """
        An iterator that returns the contents and coordinates of each cell.
        """
        for x in range(self.width):
            for y in range(self.height):
                yield self._grid.get((x, y), set()), (x, y)
    def get_neighbors(self, pos, moore, include_center=False, radius=1):
        """
        Return a list of neighbors to a certain point.
        """
        neighbors = super().get_neighbors(pos, moore, include_center, radius)
        valid_neighbors = [neighbor for neighbor in neighbors if not self.out_of_bounds(neighbor)]
        neighbor_contents = [self._grid.get(neighbor_pos, set()) for neighbor_pos in valid_neighbors]
        return [agent for sublist in neighbor_contents for agent in sublist]

    def get_cell_list_contents(self, cell_list):
        """
        Returns a list of the agents contained in the cells identified
        in `cell_list`; cells with empty content are excluded.
        """
        return [agent for pos in cell_list for agent in self._grid.get(pos, set())]
    def is_cell_empty(self, pos):
        """
        Returns a bool indicating whether the cell is empty.
        """
        return not self._grid.get(pos, set())
'''