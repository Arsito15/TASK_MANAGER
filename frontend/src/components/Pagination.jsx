export default function Pagination({ count, next, previous, onPage }) {
  if (count === 0) return null;

  const pageSize = 20;
  const totalPages = Math.ceil(count / pageSize);
  if (totalPages <= 1) return null;

  const currentPage = previous
    ? parseInt(new URLSearchParams(previous.split("?")[1]).get("page") || "1") + 1
    : next
    ? parseInt(new URLSearchParams(next.split("?")[1]).get("page") || "1") - 1
    : 1;

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        gap: "1rem",
        marginTop: "1.5rem",
      }}
    >
      <button
        className="btn-secondary"
        disabled={!previous}
        onClick={() => onPage(currentPage - 1)}
      >
        Previous
      </button>
      <span style={{ fontSize: "0.9rem", color: "var(--color-text-muted)" }}>
        Page {currentPage} of {totalPages} ({count} items)
      </span>
      <button className="btn-secondary" disabled={!next} onClick={() => onPage(currentPage + 1)}>
        Next
      </button>
    </div>
  );
}