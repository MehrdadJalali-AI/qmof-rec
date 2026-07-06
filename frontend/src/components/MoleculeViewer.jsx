import { useEffect, useRef } from "react";
import * as $3Dmol from "3dmol";

export default function MoleculeViewer({ cifText }) {
  const viewerRef = useRef(null);

  useEffect(() => {
    if (!cifText || !viewerRef.current) return;

    const container = viewerRef.current;

    container.innerHTML = "";

    let viewer = null;

    try {
      viewer = $3Dmol.createViewer(container, {
        backgroundColor: "#0a0a0b",
      });

      viewer.addModel(cifText, "cif");

      viewer.setStyle(
        {},
        {
          stick: {
            radius: 0.15,
          },
          sphere: {
            scale: 0.28,
          },
        },
      );

      viewer.zoomTo();
      viewer.render();
    } catch (error) {
      console.error("3D viewer error:", error);
    }

    return () => {
      try {
        if (viewer) {
          viewer.clear();
        }

        if (container) {
          container.innerHTML = "";
        }
      } catch (error) {
        console.error("Viewer cleanup error:", error);
      }
    };
  }, [cifText]);

  return <div ref={viewerRef} className="molecule-canvas" />;
}
