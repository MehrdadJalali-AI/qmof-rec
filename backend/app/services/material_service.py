from app.ml.interface.predictor import MaterialPredictor


predictor = MaterialPredictor()


class MaterialService:

    def predict_material(
        self,
        cif_bytes,
        filename,
    ):

        result = predictor.predict_from_cif(
            cif_bytes,
            filename,
        )

        return result


material_service = MaterialService()