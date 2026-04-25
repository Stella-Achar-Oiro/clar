interface NavBarProps {
  onNewReport?: () => void;
}

export function NavBar({ onNewReport }: NavBarProps) {
  return (
    <header
      style={{ backgroundColor: "#E05A00" }}
      className="flex items-center justify-between px-6 py-3"
    >
      <div
        className="text-white text-xl font-bold tracking-tight cursor-pointer"
        onClick={onNewReport}
        style={{ cursor: onNewReport ? "pointer" : "default" }}
      >
        CLAR
      </div>
      {onNewReport && (
        <button
          onClick={onNewReport}
          className="bg-white text-sm font-semibold px-4 py-1.5 rounded-md hover:bg-gray-100 transition-colors"
          style={{ color: "#E05A00" }}
        >
          + New Report
        </button>
      )}
    </header>
  );
}
