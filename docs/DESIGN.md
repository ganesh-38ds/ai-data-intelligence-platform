# UI/UX Design System & Style Guide

## 1. Aesthetic Concept: Midnight Glassmorphism
The platform utilizes a dark-mode, high-contrast visual hierarchy built on translucent glass surfaces, subtle gradient borders, and reactive hover transitions.

## 2. Color Palette Tokens
- **Background Slate:** `#090d16`
- **Glass Card Fill:** `rgba(15, 23, 42, 0.7)` with `backdrop-filter: blur(12px)`
- **Primary Indigo:** `#6366f1` / Hover `#4f46e5`
- **Success Emerald:** `#34d399` (Scoped Verification, High Scores)
- **Info Sky Blue:** `#38bdf8` (Retrieved Chunks, Document Badges)
- **Danger Rose:** `#f87171` (Deletions, Missing Values)
- **Text Hierarchy:** Primary `#f8fafc`, Secondary `#cbd5e1`, Muted `#94a3b8`

## 3. Component Specs
- **Document Scoping Bar:** Clean `<select>` dropdown with dynamic status pill badges.
- **Knowledge Base Manager:** CSS Grid displaying active files, chunk counts, focus buttons, and 1-click delete buttons.
- **Answer Display:** Indigo gradient container with citation pills and execution latency.