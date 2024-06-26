import math

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
            impact_chance,
            legitimacy_impact,
            incitation_threshold,
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
        self.impact_chance = impact_chance
        self.legitimacy_impact = legitimacy_impact
        self.incitation_num = 0
        self.incitation_threshold = incitation_threshold
        self.cops_in_vision = 0
        self.actives_in_vision = 0

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
                self.update_grievance_leave_jail()
            return  # no other changes or movements if agent is in jail.
        self.update_neighbors()
        self.update_estimated_arrest_probability()


        net_risk = self.risk_aversion * self.arrest_probability * self.random.randint(0,
                                                                                      self.model.max_jail_term) ** self.alpha - 0.3

        if self.condition == "Quiescent":
            if self.grievance - net_risk > self.threshold and self.actives_in_vision >= (2 * self.cops_in_vision):
                self.condition = "Active"
                self.incite_grievance()
            else:
                self.condition = "Quiescent"
        else:
            if self.grievance - net_risk < self.threshold or self.cops_in_vision >= 1:
                self.condition = "Quiescent"

        # making arrest if incitation number greater than threshold
        if self.incitation_num > self.incitation_threshold:
            sentence = self.random.randint(0, self.model.max_jail_term)
            self.jail_sentence = sentence
            self.condition = "Quiescent"
            self.incitation_num = 0
        if self.model.movement and self.empty_neighbors:
            new_pos = self.random.choice(self.empty_neighbors)
            self.model.grid.move_agent(self, new_pos)

    def update_grievance_leave_jail(self):
        # print('grievance_before_jail: ' + str(self.grievance))
        self.grievance *= self.jail_factor
        # print('update_grievance_leave_jail: ' + str(self.grievance))

    def incite_grievance(self):
        quiescent_neighbors = []
        for agent in self.neighbors:
            if agent.breed == "citizen" and agent.condition == "Quiescent":
                quiescent_neighbors.append(agent)
        if quiescent_neighbors and self.random.randrange(0, 1.0) < self.impact_chance:
            influencee = self.random.choice(quiescent_neighbors)
            if influencee.regime_legitimacy > 0.2:  # minium regime legitimacy cannot be under 0.2
                influencee.regime_legitimacy -= self.legitimacy_impact
                self.incitation_num += 1
                # print('incite_grievance')


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
        if self.model.movement and self.empty_neighbors:
            new_pos = self.random.choice(self.empty_neighbors)
            self.model.grid.move_agent(self, new_pos)