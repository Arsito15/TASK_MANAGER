export default function ConfirmDialog({ message, onConfirm, onCancel }) {
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "rgba(0,0,0,0.3)",
        zIndex: 100,
      }}
      onClick={onCancel}
    >
      <div
        className="card"
        style={{ maxWidth: 400, textAlign: "center" }}
        onClick={(e) => e.stopPropagation()}
      >
        <p style={{ marginBottom: "1.5rem" }}>{message}</p>
        <div style={{ display: "flex", gap: "0.75rem", justifyContent: "center" }}>
          <button className="btn-secondary" onClick={onCancel}>
            Cancel
          </button>
          <button className="btn-danger" onClick={onConfirm}>
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}