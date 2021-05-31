module.exports = {
    tokenSecret: process.env.TOKEN_SECRET || 'A hard to guess string 555',
    providers: {
        'google': {
            clientId: process.env.GOOGLE_CLIENTID || '255148626257-q0vpd72frmemvfurnrbno2o1l28a2v3k.apps.googleusercontent.com',
            secret: process.env.GOOGLE_SECRET || 'VY6E0UQjg_OfOAsbFwgx8GRq'
        }
    }
};