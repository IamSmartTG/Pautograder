import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Submit from './pages/Submit'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/problem/:id" element={<Submit />} />
      </Routes>
    </BrowserRouter>
  )
}
