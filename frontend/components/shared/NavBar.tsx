import { useRouter } from "next/router";

interface NavBarProps {
  showNewReport?: boolean;
}

export function NavBar({ showNewReport = false }: NavBarProps) {
  const router = useRouter();

  return (
    <header
      style={{ backgroundColor: "#1B2A4A" }}
      className="flex items-center justify-between px-6 py-3"
    >
      <div
        className="text-white text-xl font-bold tracking-tight cursor-pointer"
        onClick={() => router.push("/")}
      >
        CLAR
      </div>
      {showNewReport && (
        <button
          onClick={() => router.push("/")}
          className="bg-white text-navy text-sm font-semibold px-4 py-1.5 rounded-md hover:bg-gray-100 transition-colors"
          style={{ color: "#1B2A4A" }}
        >
          + New Report
        </button>
      )}
    </header>
  );
}
