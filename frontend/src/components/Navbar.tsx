import { NavLink, useNavigate } from "react-router-dom";

export default function Navbar({ clinicianName }: { clinicianName: string }) {
  const navigate = useNavigate();

  function logout() {
    localStorage.removeItem("access_token");
    navigate("/login");
  }

  const tabs = [
    { to: "/dashboard", label: "Consultations", icon: "📋" },
    { to: "/patients", label: "Patients", icon: "👥" },
    { to: "/profile", label: "Profile", icon: "👤" },
  ];

  return (
    <nav className="flex items-center justify-between px-6 py-4 border-b border-border">
      <span className="font-semibold text-lg">Ambient AI</span>
      <div className="flex gap-2">
        {tabs.map((t) => (
          <NavLink
            key={t.to}
            to={t.to}
            className={({ isActive }) =>
              `chip flex items-center gap-1 ${isActive ? "chip-selected" : ""}`
            }
          >
            <span>{t.icon}</span> {t.label}
          </NavLink>
        ))}
        <button onClick={logout} className="chip">
          ⏻ Log Out
        </button>
      </div>
      <span className="text-sm text-gray-400">{clinicianName}</span>
    </nav>
  );
}
