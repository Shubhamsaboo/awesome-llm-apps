import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import Articles from './pages/Articles';
import ArticleDetail from './pages/ArticleDetail';
import Podcasts from './pages/Podcasts';
import PodcastDetail from './pages/PodcastDetail';
import Sources from './pages/Sources';
import SourceDetail from './pages/SourceDetail';
import SourceEdit from './pages/SourceEdit';
import StudioLanding from './pages/StudioLanding';
import StudioChat from './pages/StudioChat';
import Voyager from './pages/Voyager';
import SocialMedia from './pages/SocialMedia';
import SocialMediaDetail from './pages/SocialMediaDetail';

const AppLayout = ({ children }) => {
  const location = useLocation();
  const isStudioPage = location.pathname.startsWith('/studio');
  if (isStudioPage) {
    return <>{children}</>;
  }
  return (
    <>
      <Navbar />
      <div className="container mx-auto px-4 py-8 flex-grow">{children}</div>
      <Footer />
    </>
  );
};

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-gray-200 flex flex-col">
        <Routes>
          <Route path="/studio" element={<StudioLanding />} />
          <Route path="/studio/chat/:sessionId" element={<StudioChat />} />
          <Route
            path="/"
            element={
              <AppLayout>
                <Home />
              </AppLayout>
            }
          />
          <Route
            path="/articles"
            element={
              <AppLayout>
                <Articles />
              </AppLayout>
            }
          />
          <Route
            path="/articles/:articleId"
            element={
              <AppLayout>
                <ArticleDetail />
              </AppLayout>
            }
          />
          <Route
            path="/podcasts"
            element={
              <AppLayout>
                <Podcasts />
              </AppLayout>
            }
          />
          <Route
            path="/podcasts/:identifier"
            element={
              <AppLayout>
                <PodcastDetail />
              </AppLayout>
            }
          />
          <Route
            path="/sources"
            element={
              <AppLayout>
                <Sources />
              </AppLayout>
            }
          />
          <Route
            path="/sources/new"
            element={
              <AppLayout>
                <SourceEdit />
              </AppLayout>
            }
          />
          <Route
            path="/sources/:sourceId/edit"
            element={
              <AppLayout>
                <SourceEdit />
              </AppLayout>
            }
          />
          <Route
            path="/sources/:sourceId"
            element={
              <AppLayout>
                <SourceDetail />
              </AppLayout>
            }
          />
          <Route
            path="/voyager"
            element={
              <AppLayout>
                <Voyager />
              </AppLayout>
            }
          />
          <Route
  path="/social-media"
  element={
    <AppLayout>
      <SocialMedia />
    </AppLayout>
  }
/>
<Route
  path="/social-media/:postId"
  element={
    <AppLayout>
      <SocialMediaDetail />
    </AppLayout>
  }
/>
        </Routes>
      </div>
    </Router>
  );
}

export default App;
