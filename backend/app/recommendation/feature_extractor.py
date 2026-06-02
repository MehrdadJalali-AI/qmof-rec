import numpy as np

from app.utils.json_utils import (
    sanitize_number,
)


class FeatureExtractor:


    def extract(

        self,

        material,

    ):

        band_gap = sanitize_number(

            material.get(

                "band_gap",

                0,

            ),

            default=0,

        )

        density = sanitize_number(

            material.get(

                "density",

                0,

            ),

            default=0,

        )

        void_fraction = sanitize_number(

            material.get(

                "void_fraction",

                0,

            ),

            default=0,

        )


        vector = np.array(

            [

                float(band_gap),

                float(density),

                float(void_fraction),

            ],

            dtype=np.float32,

        )


        vector = np.nan_to_num(

            vector,

            nan=0,

            posinf=0,

            neginf=0,

        )

        return vector


feature_extractor = FeatureExtractor()