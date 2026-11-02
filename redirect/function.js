function handler(event) {
    return {
        statusCode: 301,
        statusDescription: 'Moved Permanently',
        headers: {
            location: { value: 'https://everything.emlynoregan.com/guide' },
            'cache-control': { value: 'public, max-age=300' }
        }
    };
}
