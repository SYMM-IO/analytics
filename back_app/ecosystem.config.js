module.exports = {
    apps: [
        {
            name: "SERVER",
            script: 'app/server.py',
            watch: [],
            env: {
                PYTHONPATH: ".",
            },
            out_file: "/dev/stdout",
        },
        {
            name: "Snapshot BNB_8_2",
            script: 'app/snapshot.py',
            watch: [],
            env: {
                PYTHONPATH: ".",
                TENANT: "BNB_8_2"
            },
            out_file: "/dev/stdout",
        },
        {
            name: "Snapshot BASE_8_2",
            script: 'app/snapshot.py',
            watch: [],
            env: {
                PYTHONPATH: ".",
                TENANT: "BASE_8_2"
            },
            out_file: "/dev/stdout",
        },
        {
            name: "Load stats messages",
            script: 'app/stat_bots_loader.py',
            watch: [],
            env: {
                PYTHONPATH: ".",
            },
            out_file: "/dev/stdout",
        },
    ],
};
