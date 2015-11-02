module.exports = function (grunt) {
    grunt.initConfig({
        uglify: {
            js: {
            	/* uncomment these for debugging [there should be a better way of doing this...]
            	options: {
            		beautify: true,
            		mangle: false
            	},
            	/*/
                files: {
                    'assets/js/site.js': [
                        'assets/js/modernizr.js',
                        'assets/js/polyfills.js',
                        'assets/js/scripts.js',
                    ],
                },
            },
        },

        sass: {
            site: {
                options: {
                    style: 'compressed',
                },
                files: {
                    'assets/css/site.css': [
                        'assets/sass/public.sass',
                    ],
                }
            },
        },

        filerev: {
            options: {
                encoding: 'utf8',
                algorithm: 'sha256',
                length: 8,
            },
            images: {
                src: 'assets/images/*.{jpg,png,svg}',
                dest: 'weasyl/static/images',
            },
            js: {
                src: 'assets/js/site.js',
                dest: 'weasyl/static/js',
            },
            css: {
                src: 'assets/css/site.css',
                dest: 'weasyl/static/style',
            },
        },

        filerev_assets: {
            dist: {
                options: {
                    dest: 'weasyl/assets.json',
                    cwd: 'weasyl/',
                },
            },
        },

        usemin: {
            css: ['assets/css/site.css'],
        },

        watch: {
            images: {
                files: ['assets/images/*.{jpg,png,svg}'],
                tasks: ['filerev:images', 'usemin', 'filerev', 'filerev_assets'],
            },
            js: {
                files: ['assets/js/{scripts,modernizr,polyfills}.js'],
                tasks: ['uglify', 'filerev', 'filerev_assets'],
            },
            sass: {
                files: ['assets/sass/*.sass'],
                tasks: ['sass', 'filerev:images', 'filerev:js', 'usemin', 'filerev:css', 'filerev_assets'],
            },
        },
    });

    grunt.loadNpmTasks('grunt-filerev');
    grunt.loadNpmTasks('grunt-filerev-assets');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-sass');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-usemin');

    grunt.registerTask('default', [
        'uglify',
        'sass',
        'filerev:images',
        'filerev:js',
        'usemin',
        'filerev:css',
        'filerev_assets',
    ]);
};
