# Ignacio Jimenez - Personal Website

My personal website hosted on GitHub Pages, available at [ignacio.jimenezpi.com](https://ignacio.jimenezpi.com).

## Projects

### [Music Portfolio](/music)
A minimalist music portfolio to share some of my music projects, available at [ignacio.jimenezpi.com/music](https://ignacio.jimenezpi.com/music).

### [Photography Portfolio](/photography)
A minimalist photography portfolio available at [ignacio.jimenezpi.com/photography](https://ignacio.jimenezpi.com/photography).

## Development

Each project has its own README with detailed setup and development instructions.

### Building CSS

```bash
# Install dependencies
npm install

# Build all CSS files
npm run build:css:all

# Watch CSS files during development
npm run watch:css:all        # Watch all CSS files
npm run watch:css:music      # Watch only music CSS
npm run watch:css:photography   # Watch only photography CSS
```

### VS Code Integration

To watch CSS files in VS Code:

1. Using Command Palette:
   - Press `Cmd+Shift+P`
   - Type "Tasks: Run Task"
   - Select "Watch CSS"

2. Using Keyboard Shortcut:
   - Press `Cmd+Shift+W` to start watching CSS files

The task will automatically install dependencies if needed.

**Important**: Always run `npm run build:css:all` before committing changes. The generated CSS files need to be committed for GitHub Pages to work correctly.
