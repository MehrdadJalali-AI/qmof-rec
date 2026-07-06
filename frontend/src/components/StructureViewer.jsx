import { useEffect } from "react";

import { Viewer } from "molstar/build/viewer/molstar";

export default function StructureViewer({
  qmofId,

  onClose,
}) {
  useEffect(() => {
    const viewer = new Viewer(
      "molstar-container",

      {
        layoutIsExpanded: false,

        layoutShowControls: true,

        layoutShowSequence: false,

        layoutShowLog: false,

        layoutShowLeftPanel: false,
      },
    );

    viewer.loadStructureFromUrl(
      `${import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"}/materials/${qmofId}/structure`,

      "mmcif",

      false,
    );

    return () => {
      viewer.dispose();
    };
  }, [qmofId]);

  return (
    <div className="structure-wrapper">
      <button className="close-btn" onClick={onClose}>
        ✕
      </button>

      <div
        id="molstar-container"
        style={{
          width: "100%",

          height: "400px",
        }}
      ></div>
    </div>
  );
}
