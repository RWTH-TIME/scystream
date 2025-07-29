type TabData = {
  key: string,
  label: string,
}

type TabsProps = {
  tabs: TabData[],
  activeTab: string,
  setActiveTab: React.Dispatch<React.SetStateAction<string>>,
}

export default function Tabs({
  tabs,
  activeTab,
  setActiveTab
}: TabsProps) {
  return (
    <div className="flex items-center border-b sticky bg-white z-10">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          className={`px-4 py-3 font-medium text-sm ${activeTab === tab.key
            ? "border-b-2 border-blue-600 text-blue-600"
            : "text-gray-600 hover:text-blue-600"
            }`}
          onClick={() => setActiveTab(tab.key)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}
