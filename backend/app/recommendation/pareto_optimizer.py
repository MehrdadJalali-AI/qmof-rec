class ParetoOptimizer:


    def rank(
        self,
        materials,
    ):

        materials = sorted(

            materials,

            key=lambda x:

            x["final_score"],

            reverse=True,

        )

        return materials


pareto_optimizer = ParetoOptimizer()