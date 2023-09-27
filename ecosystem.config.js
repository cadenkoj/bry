module.exports = {
    apps: [
        {
            name: 'bry',
            script: 'main.py',
            interpreter: 'python3.11',
            instances: 1,
            out_file: 'logs/out.log',
            error_file: 'logs/err.log'
        }
    ]
};
