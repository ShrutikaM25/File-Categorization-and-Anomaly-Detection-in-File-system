import { Link, useLocation } from "react-router-dom"
import { BiSolidCategory, BiHome } from "react-icons/bi"
import { GrAlert } from "react-icons/gr"
import { SiJfrogpipelines } from "react-icons/si"
import { MdDashboard, MdKeyboardArrowRight } from "react-icons/md"

const Sidebar = ({ isOpen }) => {
  const location = useLocation()

  // Check if the current path matches the link
  const isActive = (path) => {
    return location.pathname === path
  }

  // Check if a path is part of the current path (for parent menus)
  const isPartOfPath = (path) => {
    return location.pathname.startsWith(path)
  }

  return (
    <aside
      className={`fixed left-0 w-64 bg-purple-900 text-white transform mt-16 h-[calc(100vh-4rem)] shadow-lg ${
        isOpen ? "translate-x-0" : "-translate-x-full"
      } md:translate-x-0 transition-transform duration-300 ease-in-out md:w-64 z-40`}
    >
      <div className="p-5 text-lg font-semibold flex items-center">
        <span className="bg-purple-700 h-8 w-8 rounded-md flex items-center justify-center mr-3">
          <span className="text-white text-sm font-bold">AD</span>
        </span>
        <span>Navigation</span>
      </div>

      <div className="px-3">
        <div className="h-px bg-purple-700/50 w-full"></div>
      </div>

      <div className="p-4">
        <ul className="space-y-1">
          <li>
            <Link
              to="/"
              className={`flex items-center space-x-3 p-3 rounded-lg transition-colors ${
                isActive("/") ? "bg-purple-700 text-white" : "text-purple-100 hover:bg-purple-700/50"
              }`}
            >
              <BiHome className="text-lg" />
              <span>Home</span>
            </Link>
          </li>

          <li>
            <Link
              to="/dashboard"
              className={`flex items-center space-x-3 p-3 rounded-lg transition-colors ${
                isActive("/dashboard") ? "bg-purple-700 text-white" : "text-purple-100 hover:bg-purple-700/50"
              }`}
            >
              <MdDashboard className="text-lg" />
              <span>Dashboard</span>
            </Link>
          </li>

          <li>
            <Link
              to="/classify"
              className={`flex items-center space-x-3 p-3 rounded-lg transition-colors ${
                isActive("/classify") ? "bg-purple-700 text-white" : "text-purple-100 hover:bg-purple-700/50"
              }`}
            >
              <BiSolidCategory className="text-lg" />
              <span>File Classifier</span>
            </Link>
          </li>

          <li className="pt-2">
            <div className="flex flex-col">
              <Link
                to="/anomaly"
                className={`flex items-center justify-between p-3 rounded-lg transition-colors ${
                  isPartOfPath("/anomaly") ? "bg-purple-700 text-white" : "text-purple-100 hover:bg-purple-700/50"
                }`}
              >
                <div className="flex items-center space-x-3">
                  <GrAlert className={`text-lg ${isPartOfPath("/anomaly") ? "filter-white" : ""}`} />
                  <span>Anomaly Detector</span>
                </div>
                <MdKeyboardArrowRight
                  className={`transform transition-transform ${isPartOfPath("/anomaly") ? "rotate-90" : ""}`}
                />
              </Link>

              {/* Submenu */}
              <div
                className={`mt-1 ml-4 pl-4 border-l border-purple-600 space-y-1 ${isPartOfPath("/anomaly") ? "block" : "hidden"}`}
              >
                <Link
                  to="/anomaly/run-pipeline"
                  className={`flex items-center space-x-3 p-2 rounded-lg transition-colors ${
                    isActive("/anomaly/run-pipeline")
                      ? "bg-orange-500 text-white"
                      : "text-purple-200 hover:bg-purple-700/30"
                  }`}
                >
                  <SiJfrogpipelines className="text-sm" />
                  <span className="text-sm">Run Pipeline</span>
                </Link>
              </div>
            </div>
          </li>
        </ul>
      </div>

      {/* Bottom section with user info */}
      <div className="absolute bottom-0 left-0 right-0 p-4">
        <div className="px-3 py-2">
          <div className="h-px bg-purple-700/50 w-full mb-4"></div>
          <div className="flex items-center space-x-3">
            <div className="h-8 w-8 rounded-full bg-purple-600 flex items-center justify-center">
              <span className="text-white text-sm font-bold">U</span>
            </div>
            <div>
              <p className="text-sm font-medium text-white">User</p>
              <p className="text-xs text-purple-300">Admin</p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar

