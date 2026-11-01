import React, { useEffect, useState } from 'react';
import StudioApp from './studio/StudioApp';

// The earlier company dashboards stay reachable at #/legacy; the studio is the app.
const LegacyApp = React.lazy(() => import('./App'));

const isLegacy = () => window.location.hash.startsWith('#/legacy');

export const Root: React.FC = () => {
  const [legacy, setLegacy] = useState(isLegacy);

  useEffect(() => {
    const onChange = () => setLegacy(isLegacy());
    window.addEventListener('hashchange', onChange);
    return () => window.removeEventListener('hashchange', onChange);
  }, []);

  if (legacy) {
    return (
      <React.Suspense fallback={null}>
        <LegacyApp />
      </React.Suspense>
    );
  }
  return <StudioApp />;
};

export default Root;
