from app.ml.interface.predictor import MaterialPredictor

predictor = MaterialPredictor()


class MaterialService:

    def predict_material(self, cif_bytes: bytes, filename: str):
        return predictor.predict_from_cif(cif_bytes, filename)


material_service = MaterialService()
