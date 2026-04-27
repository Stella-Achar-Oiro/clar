interface NavBarProps {
  onNewReport?: () => void;
  onMenuToggle?: () => void;
  menuOpen?: boolean;
}

export function NavBar({ onNewReport, onMenuToggle, menuOpen }: NavBarProps) {
  return (
    <header
      style={{ backgroundColor: "#E05A00" }}
      className="flex items-center justify-between px-4 py-3 flex-shrink-0"
    >
      <div className="flex items-center gap-3">
        {onMenuToggle && (
          <button
            onClick={onMenuToggle}
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            className="text-white md:hidden p-1 rounded"
          >
            {menuOpen ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            )}
          </button>
        )}
        <div
          onClick={onNewReport}
          style={{ cursor: onNewReport ? "pointer" : "default" }}
        >
          <div className="text-white text-xl font-bold tracking-tight">CLAR</div>
          <div className="text-white text-xs opacity-75 tracking-wide">Your health reports, finally clear.</div>
        </div>
      </div>
      {onNewReport && (
        <button
          onClick={onNewReport}
          className="bg-white text-sm font-semibold px-3 py-1.5 rounded-md hover:bg-gray-100 transition-colors"
          style={{ color: "#E05A00" }}
        >
          + New Report
        </button>
      )}
    </header>
  );
}
