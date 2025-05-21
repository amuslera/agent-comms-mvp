# Bluelabel Agent OS - Web Dashboard

A modern web interface for monitoring and managing the Bluelabel Agent OS multi-agent system.

## Features

- **Dashboard**: Overview of system status and key metrics
- **Agents Management**: View and manage connected agents
- **Responsive Design**: Works on desktop and tablet devices
- **Real-time Updates**: Live status updates for agents and tasks

## Prerequisites

- Node.js 16.14.0 or higher
- npm 7.0.0 or higher

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/amuslera/agent-comms-mvp.git
   cd agent-comms-mvp/apps/web
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```

4. **Open in browser**
   The application will be available at [http://localhost:5173](http://localhost:5173)

## Available Scripts

- `npm run dev` - Start the development server
- `npm run build` - Build the application for production
- `npm run preview` - Preview the production build locally
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## Project Structure

```
src/
├── components/     # Reusable UI components
├── pages/          # Page components
├── hooks/          # Custom React hooks
├── api/            # API client and service functions
└── App.tsx         # Main application component
```

## Styling

This project uses [Tailwind CSS](https://tailwindcss.com/) for styling. The configuration can be found in `tailwind.config.js`.

## Linting and Formatting

- ESLint is used for code linting
- Prettier is used for code formatting
- TypeScript is used for type checking

## Contributing

1. Create a new branch for your feature or bugfix
2. Make your changes
3. Run the linter and tests
4. Submit a pull request

## License

MIT
