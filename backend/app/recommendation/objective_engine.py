class ObjectiveEngine:


    def objectives(
        self,
        weights,
    ):

        return {

            "maximize_porosity":

                weights.get(
                    "porosity",
                    0
                ),

            "maximize_bandgap":

                weights.get(
                    "band_gap",
                    0
                ),

            "minimize_density":

                weights.get(
                    "density",
                    0
                ),

        }


objective_engine = ObjectiveEngine()