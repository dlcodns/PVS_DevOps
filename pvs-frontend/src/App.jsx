import './App.css';
import GrafanaPanel from './components/GrafanaPanel';
import VideoPanel from './components/VideoPanel';
import MapPanel from './components/MapPanel';
import LogPanel from './components/LogPanel';

function App(){
  return (
    <div className="dashboard">
      <div className="grid-container">
        <div className='panel'>
          <VideoPanel />
        </div>
        <div className='panel'>
          <GrafanaPanel />
        </div>
        <div className='panel'>
          <MapPanel />
        </div>
        <div className='panel'>
          <LogPanel />
        </div>
      </div>
    </div>
  );
}

export default App;