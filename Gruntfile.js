module.exports = function (grunt) {
    grunt.initConfig({
        uglify: {
            js: {
                files: {
                    'assets/js/site.js': [
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
                dest: 'weasyl/static',
            },
            css: {
                src: 'assets/css/site.css',
                dest: 'weasyl/static',
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
    });

    grunt.loadNpmTasks('grunt-filerev');
    grunt.loadNpmTasks('grunt-filerev-assets');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-sass');

    grunt.registerTask(
        'default', ['uglify', 'sass', 'filerev', 'filerev_assets']);
};
