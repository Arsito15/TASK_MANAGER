export default function ConfirmDialog({ message, onConfirm, onCancel }) {
  return (
    <div className="confirm-overlay" onClick={onCancel}>
      <div
        className="card confirm-dialog"
        onClick={(e) => e.stopPropagation()}
      >
        <p style={{ marginBottom: "1.5rem", fontSize: "0.95rem", color: "var(--color-text-secondary)" }}>
          {message}
        </p>
        <div style={{ display: "flex", gap: "0.5rem", justifyContent: "center" }}>
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