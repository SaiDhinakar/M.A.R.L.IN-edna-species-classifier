import React from 'react';
import Header from './Header';
import Sidebar from './Sidebar';

const Layout = ({ children, title = "Dashboard" }) => {
  return (
    <div className="min-h-screen bg-background">
      <div className="flex">
        <Sidebar />
        <div className="flex-1 flex flex-col lg:ml-0">
          <Header title={title} />
          <main className="flex-1 p-6">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
};

export default Layout;