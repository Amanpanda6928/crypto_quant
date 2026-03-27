import React from 'react';

const Sidebar = ({ isOpen, onClose }) => {
  const menuItems = [
    { label: 'Dashboard', icon: '📊', active: true },
    { label: 'Signals', icon: '📈', active: false },
    { label: 'Portfolio', icon: '💼', active: false },
    { label: 'Analytics', icon: '📊', active: false },
    { label: 'Settings', icon: '⚙️', active: false }
  ];

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 text-white transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="flex items-center justify-center h-16 bg-gray-800">
          <h1 className="text-xl font-bold">CryptoQuant Pro</h1>
        </div>

        <nav className="mt-8">
          <div className="px-4 space-y-2">
            {menuItems.map((item, index) => (
              <div
                key={index}
                className={`flex items-center space-x-3 px-4 py-3 rounded-lg cursor-pointer transition-colors ${
                  item.active
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                <span className="text-lg">{item.icon}</span>
                <span className="font-medium">{item.label}</span>
              </div>
            ))}
          </div>
        </nav>

        {/* System Status */}
        <div className="absolute bottom-0 left-0 right-0 p-4 bg-gray-800">
          <div className="flex items-center space-x-2 text-green-400">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-sm">System Online</span>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;