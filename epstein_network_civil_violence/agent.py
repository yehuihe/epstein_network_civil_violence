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
        rumor_effect,
        pretense = False,
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
            rumor_effect: Network rumor effect posed by active agents. 
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
        self.rumor_effect = rumor_effect
        self.pretense = pretense
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
        print("###############")
        print(self.pos)
        print(actives_in_vision, cops_in_vision)
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
            return  # no other changes or movements if agent is in jail.
        self.update_neighbors()
        self.update_estimated_arrest_probability()
        print(self.arrest_probability)
        net_risk = self.risk_aversion * self.arrest_probability * self.jail_sentence ** self.alpha
        if self.condition == "Quiescent":
            if self.grievance - net_risk > self.threshold and self.actives_in_vision >= (1 * self.cops_in_vision):
            # if self.grievance - net_risk > self.threshold:
                self.condition = "Active"
            else:
                self.condition = "Quiescent"
        else:
            if self.grievance - net_risk < self.threshold or self.cops_in_vision >= 1:
                self.condition = "Quiescent"


        if self.model.movement and self.empty_neighbors:
            new_pos = self.random.choice(self.empty_neighbors)
            self.model.grid.move_agent(self, new_pos)

    def spreading_rumor(self):
        # TODO
        pass


class Police(Cop):
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
            # print(arrestee.arrest_probability)
            if self.random.random()<arrestee.arrest_probability:
                sentence = self.random.randint(0, self.model.max_jail_term)
                arrestee.jail_sentence = sentence
                arrestee.condition = "Quiescent"
        if self.model.movement and self.empty_neighbors:
            new_pos = self.random.choice(self.empty_neighbors)
            self.model.grid.move_agent(self, new_pos)
