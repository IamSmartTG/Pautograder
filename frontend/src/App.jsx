import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import Home from './pages/Home'
import Submit from './pages/Submit'

function TopBar() {
  return (
    <header className="topbar">
      <Link to="/" className="brand">
        <span className="brand__mark">P</span>
        <span className="brand__name">pautograder</span>
      </Link>
      <span className="topbar__status"><span className="dot" /> sandbox ready</span>
    </header>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <TopBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/problem/:id" element={<Submit />} />
      </Routes>
    </BrowserRouter>
  )
}
