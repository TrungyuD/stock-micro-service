// ecosystem.config.js — PM2 process manager config for stock-micro-service
// Usage: pm2 start ecosystem.config.js
const path = require('path');
const ROOT = __dirname;

module.exports = {
  apps: [
    {
      name: 'stock-gateway',
      cwd: path.join(ROOT, 'gateway'),
      script: 'dist/main.js',
      interpreter: 'node',
      instances: 1,
      exec_mode: 'fork',
      env: {
        NODE_ENV: 'development',
        GATEWAY_PORT: 5301,
      },
      env_production: {
        NODE_ENV: 'production',
        GATEWAY_PORT: 5301,
      },
      watch: false,
      max_memory_restart: '512M',
      error_file: path.join(ROOT, 'logs', 'gateway-error.log'),
      out_file: path.join(ROOT, 'logs', 'gateway-out.log'),
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },
    {
      name: 'stock-informer',
      cwd: path.join(ROOT, 'services', 'informer'),
      script: 'src/server.py',
      interpreter: path.join(ROOT, 'services', 'informer', '.venv', 'bin', 'python3'),
      instances: 1,
      exec_mode: 'fork',
      env: {
        PYTHONPATH: path.join(ROOT, 'services', 'informer', 'src'),
        GRPC_HOST: '0.0.0.0',
        GRPC_PORT: 5302,
        LOG_LEVEL: 'INFO',
      },
      watch: false,
      max_memory_restart: '256M',
      error_file: path.join(ROOT, 'logs', 'informer-error.log'),
      out_file: path.join(ROOT, 'logs', 'informer-out.log'),
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },
    {
      name: 'stock-analytics',
      cwd: path.join(ROOT, 'services', 'analytics'),
      script: 'src/server.py',
      interpreter: path.join(ROOT, 'services', 'analytics', '.venv', 'bin', 'python3'),
      instances: 1,
      exec_mode: 'fork',
      env: {
        PYTHONPATH: path.join(ROOT, 'services', 'analytics', 'src'),
        GRPC_HOST: '0.0.0.0',
        GRPC_PORT: 5303,
        LOG_LEVEL: 'INFO',
      },
      watch: false,
      max_memory_restart: '256M',
      error_file: path.join(ROOT, 'logs', 'analytics-error.log'),
      out_file: path.join(ROOT, 'logs', 'analytics-out.log'),
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },
  ],
};
