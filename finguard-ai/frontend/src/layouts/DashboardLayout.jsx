import React, { useState } from 'react';
import { Sidebar } from '../components/navigation/Sidebar';
import { Topbar } from '../components/navigation/Topbar';

export function DashboardLayout({ children }) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex">
      <Sidebar
        isCollapsed={isCollapsed}
        toggleSidebar={() => setIsCollapsed(!isCollapsed)}
        mobileOpen={mobileSidebarOpen}
        closeMobileSidebar={() => setMobileSidebarOpen(false)}
      />
      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-30 lg:hidden"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar
          isCollapsed={isCollapsed}
          toggleMobileSidebar={() =>
            setMobileSidebarOpen((prev) => !prev)
          } />
        <main className={`flex-1 pt-20 pb-8 px-4 md:px-6 xl:px-10 transition-all duration-300 ${isCollapsed ? 'lg:ml-20' : 'lg:ml-64'
          }`}>
          <div className="w-full max-w-[1700px] mx-auto space-y-8 animate-fade-in">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
