(function() {
    'use strict';

    var forEach = Array.prototype.forEach;
    var DOMTokenList;

    var classListSupported = document.documentElement.classList && (function () {
        var testElement = document.createElement('div');
        testElement.classList.toggle('test', false);
        return !testElement.classList.contains('test');
    })();

    if (!classListSupported && Object.defineProperty && typeof HTMLElement !== 'undefined') {
        DOMTokenList = function DOMTokenList() {
            throw new TypeError('Illegal constructor.');
        };

        DOMTokenList.prototype.add = function() {
            var classes = this._element.className.match(/\S+/g) || [];

            for (var i = 0; i < arguments.length; i++) {
                var class_ = arguments[i];

                if (classes.indexOf(class_) === -1) {
                    this._element.className += ' ' + class_;
                }
            }
        };

        DOMTokenList.prototype.remove = function() {
            var classes = this._element.className.match(/\S+/g) || [];
            var remove = Array.prototype.slice.call(arguments);

            this._element.className = classes.filter(function(existingClass) {
                return remove.indexOf(existingClass) === -1;
            }).join(' ');
        };

        DOMTokenList.prototype.toggle = function(class_, to) {
            if (to === undefined) {
                to = !this.contains(class_);
            }

            if (to) {
                this.add(class_);
            } else {
                this.remove(class_);
            }

            return to;
        };

        DOMTokenList.prototype.contains = function(class_) {
            var classes = this._element.className.match(/\S+/g) || [];

            return classes.indexOf(class_) !== -1;
        };

        Object.defineProperty(DOMTokenList.prototype, 'length', {
            get: function() {
                var classes = this._element.className.match(/\S+/g) || [];

                return classes.length;
            }
        });

        Object.defineProperty(HTMLElement.prototype, 'classList', {
            get: function() {
                return Object.create(DOMTokenList.prototype, {
                    _element: {
                        value: this,
                        writable: false
                    }
                });
            }
        });
    }


    // helper function: nodelist to array
    function toArray(obj) {
        var array = [];
        for (var i = obj.length >>> 0; i--;) {
            array[i] = obj[i];
        }
        return array;
    }


    // helper functions: get parents
    function getParents(obj) {
        var parents = [];
        while ( obj !== document.documentElement ) {
            parents.push(obj);
            obj = obj.parentNode;
        }
        return parents;
    }

    function getParentsByTagName(obj, tag) {
        tag = tag.toLowerCase();

        return getParents(obj).filter(function(el) {
            return el.tagName.toLowerCase() === tag;
        });
    }

    function getParentsByClassName(obj, cl) {
        return getParents(obj).filter(function(el) {
            return el.classList.contains(cl);
        });
    }


    // debounced window resize event
    (function() {
        if (!window.addEventListener || !document.createEvent) {
            return;
        }

        var event = document.createEvent('Event');
        event.initEvent('resize:end', false, false);

        function dispatchResizeEndEvent() {
            return window.dispatchEvent(event);
        }

        var initialOrientation = window.orientation;
        var resizeDebounceTimeout = null;

        function debounce() {
            var currentOrientation = window.orientation;

            if (currentOrientation !== initialOrientation) {
                dispatchResizeEndEvent();
                initialOrientation = currentOrientation;
            } else {
                clearTimeout(resizeDebounceTimeout);
                resizeDebounceTimeout = setTimeout(dispatchResizeEndEvent, 100);
            }
        }

        window.addEventListener('resize', debounce, false);
    })();


    // weasyl mosaic thumbnail layout
    function wzlMosaic(el) {
        var maxBlockWidth = 96,
            aspectRatios = [0.33, 0.66, 1, 1.5, 3],
            grid = [],
            tiles, tileCount, containerWidth, blockDim, columnCount, globalOffset;

        el.classList.add('enabled');

        // create a new grid row of empty cells at specified y position
        function newGridRow(row) {
            grid[row] = [];
            for ( var i = 0; i < columnCount; i++ ) {
                grid[row].push(0);
            }
            console.log('created new grid row at ' + row);
        }

        // set up container properties
        function setupContainer() {
            console.log('setting up container...');
            globalOffset = 0;

            el.setAttribute('style', 'display: block !important;');  // infinite loop if no width to go on
            el.parentNode.setAttribute('style', 'display: block !important;');
            containerWidth = el.offsetWidth;
            el.removeAttribute('style');
            el.parentNode.removeAttribute('style');

            console.log('container width: ' + containerWidth);
            columnCount = Math.ceil(containerWidth / maxBlockWidth);
            blockDim = Math.floor(containerWidth / columnCount);

            // wipe existing grid (if any) and create three empy grid rows to work within
            grid.length = 0;
            console.log('wiped existing grid');
            newGridRow(0); newGridRow(1); newGridRow(2);
            console.log('created starter rows');

            // ragged top - randomize layout of first two rows
            if ( el.classList.contains('ragged') ) {
                for (var d = 0; d < columnCount; d++) {
                    if (Math.random() < 0.5) {
                        grid[0][d] = 1;
                        if (Math.random() < 0.4) {
                            grid[1][d] = 1;
                        }
                    }
                }
                console.log('created ragged gaps');
            }
        }

        // process tile properties
        function setupTiles(offset) {
            console.log('setting up tiles ...');
            if ( !offset ) { offset = 0; }
            tiles = toArray(el.getElementsByClassName('item'));
            tileCount = tiles.length;
            console.log(tileCount + ' tiles in set');

            var offsetTiles = tiles.slice(offset);
            for ( var i = 0; i < offsetTiles.length; i++ ) {
                var thisTile = offsetTiles[i],
                    aspectRatio = parseFloat(thisTile.getAttribute('data-init-aspect')),
                    closestRatio = null,
                    thumbImage = thisTile.querySelector('.thumb').getAttribute('src'),
                    childA = thisTile.querySelector('a');
                console.log('Processing the following tile:');
                console.log(thisTile);

                // set as background image in order to let the browser handle sizing
                childA.style.backgroundImage = 'url("' + thumbImage + '")';
                console.log('backgroundImage set');

                // assign closest aspect
                for ( var j = 0; j < aspectRatios.length; j++ ) {
                    if (closestRatio === null || Math.abs(aspectRatios[j] - aspectRatio) < Math.abs(closestRatio - aspectRatio)) {
                        closestRatio = aspectRatios[j];
                    }
                }
                thisTile.setAttribute('data-snapped-aspect', closestRatio);
                thisTile.setAttribute('data-placed', 0);
                console.log('aspect ratio set: ' + closestRatio);

                // assign cell dimensions and denote resizeability
                if (closestRatio === 0.33) {
                    thisTile.setAttribute('data-sizeX', 1);
                    thisTile.setAttribute('data-sizeY', 3);
                    thisTile.setAttribute('data-resizeable2', 0);
                    thisTile.setAttribute('data-resizeable1', 0);
                } else if (closestRatio === 0.66) {
                    thisTile.setAttribute('data-sizeX', 2);
                    thisTile.setAttribute('data-sizeY', 3);
                    thisTile.setAttribute('data-resizeable2', 0);
                    thisTile.setAttribute('data-resizeable1', 1);
                    thisTile.setAttribute('data-size1X', 1);
                    thisTile.setAttribute('data-size1Y', 2);
                } else if (closestRatio === 1) {
                    thisTile.setAttribute('data-sizeX', 3);
                    thisTile.setAttribute('data-sizeY', 3);
                    thisTile.setAttribute('data-resizeable2', 1);
                    thisTile.setAttribute('data-size2X', 2);
                    thisTile.setAttribute('data-size2Y', 2);
                    thisTile.setAttribute('data-resizeable1', 1);
                    thisTile.setAttribute('data-size1X', 1);
                    thisTile.setAttribute('data-size1Y', 1);
                } else if (closestRatio === 1.5) {
                    thisTile.setAttribute('data-sizeX', 3);
                    thisTile.setAttribute('data-sizeY', 2);
                    thisTile.setAttribute('data-resizeable2', 1);
                    thisTile.setAttribute('data-size2X', 2);
                    thisTile.setAttribute('data-size2Y', 1);
                    thisTile.setAttribute('data-resizeable1', 0);
                } else if (closestRatio === 3) {
                    thisTile.setAttribute('data-sizeX', 3);
                    thisTile.setAttribute('data-sizeY', 1);
                    thisTile.setAttribute('data-resizeable2', 0);
                    thisTile.setAttribute('data-resizeable1', 0);
                }
                console.log('cell data applied to tile');
            }
        }

        // the fun part
        function mosaicLayout(isAppend) {
            console.log('Fitting tiles ...');
            var curTile = 0,
                isLookahead = false,
                posX = 0,
                posY = 0;

            // if appending to existing data, find starting row
            if (isAppend) {
                for ( var i = grid.length - 1; i >= 0; i-- ) {
                    if ( grid[i].indexOf(0) !== -1) {
                        posY = i;
                    } else {
                        break;
                    }
                }
            }

            // function to find empty spaces to the right of a given point
            function findSpaceFromPoint(posX, posY) {
                console.log('Finding space from ' + posX + ', ' + posY + ' ...');
                if (posX >= columnCount) {
                    return [false, posX];
                }
                var availableSpace = 0;

                while ( grid[posY][posX] === 1 ) {
                    if (posX >= columnCount) {
                        return [false, posX];
                    }
                    posX++;
                }
                var shiftedX = posX;

                while (posX < columnCount) {
                    availableSpace++;
                    posX++;
                    if ( grid[posY][posX] === 1 ) {
                        break;
                    }
                }

                console.log('space available: ' + availableSpace);
                return [availableSpace, shiftedX];
            }

            // function to place a tile into the grid
            function placeTile(t) {
                console.log('Placing tile into the grid ...');
                tiles[t].setAttribute('data-tilePosX', posX);
                tiles[t].setAttribute('data-tilePosY', posY);
                tiles[t].setAttribute('data-placed', 1);

                for (var i = 0; i < tileSizeX; i++) {
                    for (var j = 0; j < tileSizeY; j++) {
                        var fitX = posX + i,
                            fitY = posY + j;
                        grid[fitY][fitX] = 1;
                    }
                }

                posX += tileSizeX;
            }

            // walk through and fit each tile
            while (curTile < tileCount) {
                console.log('fitting a tile ...');

                if (isLookahead) {
                    isLookahead = false;
                } else {
                    curTile = 0;
                    for (var a = 0; a < tileCount; a++) {
                        var aa = tiles[a].getAttribute('data-placed');
                        if ( aa < 1 ) {
                            curTile = a;
                            break;
                        }
                        curTile++;
                    }
                }
                // because we mess with the iterated var
                if (curTile >= tileCount) {
                    break;
                }

                var thisTile = tiles[curTile],
                    tileSizeX = parseInt(thisTile.getAttribute('data-sizeX')),
                    tileSizeY = parseInt(thisTile.getAttribute('data-sizeY'));

                // get space available right now
                console.log('tile dimensions: ' + tileSizeX + ', ' + tileSizeY);
                var spaceAvail = findSpaceFromPoint(posX, posY);

                // if reached end of row without finding space
                while (spaceAvail[0] === false || spaceAvail[0] <= 0) {
                    posY++;
                    posX = 0;
                    newGridRow(posY + 2);
                    spaceAvail = findSpaceFromPoint(posX, posY);
                }
                posX = spaceAvail[1];

                // can this fit?
                if ( tileSizeX <= spaceAvail[0] ) {
                    console.log('found space');
                    placeTile(curTile);
                } else if ( spaceAvail[0] >= 2 && thisTile.getAttribute('data-resizeable2') == 1 ) {
                    console.log('shrank tile to 2 units wide');
                    tileSizeX = parseInt(thisTile.getAttribute('data-size2X'));
                    tileSizeY = parseInt(thisTile.getAttribute('data-size2Y'));
                    thisTile.setAttribute('data-sizeX', tileSizeX);
                    thisTile.setAttribute('data-sizeY', tileSizeY);
                    placeTile(curTile);
                } else if ( spaceAvail[0] >= 1 && thisTile.getAttribute('data-resizeable1') == 1 ) {
                    console.log('shrank tile to 1 unit wide');
                    tileSizeX = parseInt(thisTile.getAttribute('data-size1X'));
                    tileSizeY = parseInt(thisTile.getAttribute('data-size1Y'));
                    thisTile.setAttribute('data-sizeX', tileSizeX);
                    thisTile.setAttribute('data-sizeY', tileSizeY);
                    placeTile(curTile);
                } else {
                    console.log('didn’t find space');
                    var b = 0;
                    var foundTile = false;
                    for ( b = curTile + 1; b < tileCount; b++ ) {
                        if ( tiles[b].getAttribute('data-placed') < 1 ) {
                            foundTile = true;
                            break;
                        }
                    }
                    if (foundTile) {
                        console.log('looking ahead ... ');
                        foundTile = false;
                        isLookahead = true;
                        curTile = b;
                        continue;
                    }
                    // if didn't find a suitable tile, do what we can with remaining space
                    if (posX < columnCount) {
                        console.log('advancing x position, trying again');
                        posX++;
                        continue;
                    } else {
                        console.log('making new row, trying again');
                        posX = 0;
                        posY++;
                        newGridRow(posY + 2);
                        continue;
                    }
                }
            }
        }

        // place each tile into css layout
        function drawTiles(offset) {
            console.log('placing tiles into css layout ...');
            if (!offset) {
                offset = 0;
            }

            for ( var i = offset; i < tileCount; i++ ) {
                var thisTile = tiles[i],
                    thisInfo = thisTile.querySelector('.info'),
                    thisWidth = parseInt(thisTile.getAttribute('data-sizeX')) * blockDim,
                    thisHeight = parseInt(thisTile.getAttribute('data-sizeY')) * blockDim,
                    thisPosX = parseInt(thisTile.getAttribute('data-tilePosX')) * blockDim,
                    thisPosY = parseInt(thisTile.getAttribute('data-tilePosY')) * blockDim;
                console.log(thisTile);

                thisTile.style.width = thisWidth + 'px';
                thisTile.style.height = thisHeight + 'px';
                thisTile.style.left = thisPosX + 'px';
                thisTile.style.top = thisPosY + 'px';
                console.log('applied style attributes');

                // position info tooltips
                thisInfo.style.width = (blockDim * 3) + 'px';
                thisInfo.style.marginLeft = 0;
                thisInfo.classList.remove('edge-left');
                thisInfo.classList.remove('edge-right');

                if ( thisPosX < blockDim ) {
                    thisInfo.classList.add('edge-left');
                } else if ( containerWidth - thisPosX - thisWidth < blockDim ) {
                    thisInfo.classList.add('edge-right');
                } else {
                    thisInfo.style.marginLeft = (-blockDim * 3/2) + 'px';
                }
                console.log('positioned info tooltip');

                globalOffset++;
            }

            // trim grid
            console.log('trimming excess grid rows ...');
            var trimLength = 0;
            for (var n = grid.length - 1; n >= 0; n--) {
                if (grid[n].indexOf(1) !== -1) {
                    break;
                }

                trimLength++;
            }
            console.log('grid trimmed');
            // and set height of container
            el.style.height = ((grid.length - trimLength) * blockDim) + 'px';
            console.log('container height set');

            // for (var k = 0; k < grid.length; k++) {
            //     console.log(grid[k]);
            // }
        }

        // light the fuse
        console.log('starting initial run ...');
        setupContainer();
        setupTiles();
        mosaicLayout();
        drawTiles();

        // recalculate on resize
        window.addEventListener('resize:end', function() {
            console.log('resize event detected, recalculating mosaic ...');
            setupContainer();
            setupTiles();
            mosaicLayout();
            drawTiles();
        }, false);

        // hover intent
        var hoverDelay, hoverDebounce = false;
        el.addEventListener('mouseenter', function() {
            if ( !hoverDebounce ) {
                hoverDebounce = true;
                hoverDelay = setTimeout(function() {
                    el.classList.add('hovered');
                }, 940);
            }
        });
        console.log('added mouseenter handler');
        el.addEventListener('mouseleave', function() {
            hoverDebounce = false;
            clearTimeout(hoverDelay);
            el.classList.remove('hovered');
        });
        console.log('added mouseleave handler');
    }


    // generic toggles
    // <el class="toggle" data-toggle-target="[next|parentnext|css selector]" />
    function wzlToggles(el) {
        var toggleTarget = el.getAttribute('data-toggle-target'),
            targetObject = null;

        if ( toggleTarget === 'next' ) {
            targetObject = el.nextElementSibling;
        } else if ( toggleTarget === 'parentnext' ) {
            targetObject = el.parentNode.nextElementSibling;
        } else if ( toggleTarget === 'parentparentnext' ) {
            targetObject = el.parentNode.parentNode.nextElementSibling;
        }

        if ( targetObject ) {
            targetObject.classList.toggle('active');
        } else if ( toggleTarget !== null ) {
            forEach.call(document.querySelectorAll(toggleTarget), function(targetEl) {
                targetEl.classList.toggle('active');
            });
        }

        el.classList.toggle('active');
        // window.dispatchEvent(new Event('resize'));
    }


    // shared height elements
    // <el class="shared-height" data-height-group="[string]">
    (function() {
        var heightEls = document.querySelectorAll('.shared-height'),
            heightGroups = [], uniqueHeightGroups = [];

        // get height groups together
        for ( var i = 0; i < heightEls.length; i++ ) {
            heightGroups.push(heightEls[i].getAttribute('data-height-group'));
        }
        uniqueHeightGroups = heightGroups.filter(function(val, pos) {
            return heightGroups.indexOf(val) === pos;
        });

        function evenHeights() {
            var i, j, el;

            // blank slate
            for ( i = 0; i < heightEls.length; i++ ) {
                heightEls[i].style.minHeight = 'auto';
            }
            // iterate over groups
            for ( i = 0; i < uniqueHeightGroups.length; i++ ) {
                var thisHeight, lastHeight = 1, maxHeight = 2,
                    groupEls = document.querySelectorAll('.shared-height[data-height-group="' + uniqueHeightGroups[i] + '"]');
                for ( j = 0; j < groupEls.length; j++ ) {
                    el = groupEls[j];
                    thisHeight = parseInt(el.clientHeight);
                    if ( thisHeight > lastHeight ) {
                        maxHeight = thisHeight;
                    }
                    lastHeight = thisHeight;
                }
                for ( j = 0; j < groupEls.length; j++ ) {
                    el = groupEls[j];
                    el.style.minHeight = maxHeight + 'px';
                }
            }
        }

        window.addEventListener('load', evenHeights);
        window.addEventListener('resize', evenHeights);
    })();


    // active form labels
    function wzlLabels(el) {
        var input = el.getElementsByTagName('input')[0] || el.getElementsByTagName('textarea')[0];
        el.classList.add('enabled');
        function checkFilled() {
            if ( input.value !== '' ) {
                el.classList.add('has-contents');
            } else {
                el.classList.remove('has-contents');
            }
        }
        checkFilled();
        window.addEventListener('load', checkFilled);

        input.addEventListener('focus', function() {
            el.classList.add('active');
        });
        input.addEventListener('blur', function() {
            el.classList.remove('active');
            checkFilled();
        });
    }


    // art zoom
    forEach.call(document.getElementsByClassName('sub-zoom-toggle'), function(el) {
        el.addEventListener('click', function(ev) {
            ev.preventDefault();
            el.classList.toggle('active');
            document.querySelector('.page-header').classList.toggle('hide');
            document.querySelector('.page-footer').classList.toggle('hide');
            var artSiblings = document.getElementById('main').children;
            for ( var i = 0; i < artSiblings.length; i++ ) {
                if ( !artSiblings[i].classList.contains('sub-container') ) {
                    artSiblings[i].classList.toggle('hide');
                }
            }
            document.body.classList.toggle('zoomed');
        });
    });


    // modal escape listener
    (function() {
        var modals = document.getElementsByClassName('modal');
        if ( modals.length > 0 ) {
            window.addEventListener('keydown', function(ev) {
                if ( ev.keyCode === 27 ) {
                    for ( var i = 0; i < modals.length; i++ ) {
                        modals[i].classList.remove('active');
                    }
                }
            });
        }
    })();


    // resizing textareas
    function textareas(parentEl) {
        var el = parentEl.getElementsByTagName('textarea')[0],
            ref = parentEl.getElementsByClassName('resize-ref')[0],
            container = getParentsByClassName(el, 'comment-new-box')[0];

        function doCopy() {
            // copies textarea value to reference element
            // appends additional <br /> so IE respects trailing whitespace
            ref.innerHTML = el.value.replace(/\n/g, '<br />') + ' <br /> ';
        }
        doCopy();

        el.addEventListener('input', doCopy, false);

        // adds appropriate class to container element for focus visualization
        if (container) {
            el.addEventListener('focus', function() {
                container.classList.add('highlight');
            });
            el.addEventListener('blur', function() {
                if (el.value.length === 0) {
                    container.classList.remove('highlight');
                }
            });
        }
    }
    forEach.call(document.getElementsByClassName('resizing-textarea'), function(el) {
        textareas(el);
    });


    // checkbox/radio events
    function areAllChecked(els) {  // returns true if all elements in given set are checked
        for (var i = els.length >>> 0; i--;) {
            if (els[i].checked === false) {
                return false;
            }
        }
        return true;
    }
    function getCheckboxes(context) {  // gets valid checkboxes in given context
        return toArray(context.querySelectorAll('input[type="checkbox"]:not(.checkbox-parent)'));
    }
    function updateCounts() {  // updates count elements with number of checked boxes in context
        forEach.call(document.getElementsByClassName('checked-count'), function(el) {
            var checkboxes = getCheckboxes(document.querySelector(el.getAttribute('data-context')));

            var count = checkboxes.reduce(function (count, checkbox) {
                return count + checkbox.checked;
            }, 0);

            el.textContent = count + ' of ' + checkboxes.length;
        });
    }
    updateCounts();
    function triggerChange(el) {  // trigger events that fire on checkbox change
        var event = document.createEvent('HTMLEvents');
        event.initEvent('change', true, false);
        el.dispatchEvent(event);
    }
    function changeCheckboxStates(context, action) {  // change all checkboxes in context with given action
        var checkboxes = getCheckboxes(context);
        forEach.call(checkboxes, function(checkbox) {
            if (action === 'on' && !checkbox.checked) {
                checkbox.checked = true;
                triggerChange(checkbox);
            } else if (action === 'off' && checkbox.checked) {
                checkbox.checked = false;
                triggerChange(checkbox);
            } else if (action === 'invert') {
                checkbox.checked = !checkbox.checked;
                triggerChange(checkbox);
            }
        });
        updateCounts();
    }
    function changeParentLabel(el) {
        var thisLabel = getParentsByTagName(el, 'label')[0];
        thisLabel.classList.toggle('checked', el.checked);
    }
    // handle individual checkbox changes
    forEach.call(document.querySelectorAll('input[type=checkbox], input[type=radio]'), function(el) {
        var isParent = el.classList.contains('checkbox-parent'),
            isChild = el.classList.contains('checkbox-child');

        changeParentLabel(el);

        el.addEventListener('change', function() {
            // hierarchical checkboxes
            if ( isParent || isChild ) {
                var groupEl = getParentsByClassName(el, 'checkbox-group')[0],
                    parentBox = groupEl.getElementsByClassName('checkbox-parent')[0],
                    childBoxes = groupEl.getElementsByClassName('checkbox-child');

                if ( isParent ) {
                    forEach.call(childBoxes, function(childEl) {
                        childEl.checked = el.checked;
                    });
                } else if ( !el.checked ) {
                    parentBox.checked = false;
                } else if (areAllChecked(childBoxes)) {
                    parentBox.checked = true;
                }

                forEach.call([parentBox].concat(toArray(childBoxes)), function(thisBox) {
                    changeParentLabel(thisBox);
                });

            // standalone checkboxes
            } else {
                changeParentLabel(el);
            }
            updateCounts();
        });
    });
    // handle check/uncheck/invert all
    forEach.call(document.querySelectorAll('.check-all, .uncheck-all, .invert-all'), function(el) {
        var context = document.querySelector(el.getAttribute('data-context'));
        if (context) {
            if (el.classList.contains('check-all')) {
                el.addEventListener('click', function() {
                    changeCheckboxStates(context, 'on');
                });
            } else if (el.classList.contains('uncheck-all')) {
                el.addEventListener('click', function() {
                    changeCheckboxStates(context, 'off');
                });
            } else if (el.classList.contains('invert-all')) {
                el.addEventListener('click', function() {
                    changeCheckboxStates(context, 'invert');
                });
            }
        }
    });


    // sticky notification utilities
    // remove once position: sticky is supported 'enough'
    (function() {
        var el = document.getElementsByClassName('sticky')[0],
            mainCol = document.getElementsByClassName('col-layout-main')[0],
            footer = document.getElementsByClassName('page-footer')[0],
            refPos, elHeight, footerPos;

        if (!el || !mainCol || !footer) {
            return;
        }

        function checkSticky() {
            refPos = mainCol.getBoundingClientRect().top;
            footerPos = footer.getBoundingClientRect().top;

            if (refPos <= 0) {
                el.classList.add('stuck');
            } else {
                el.classList.remove('stuck');
            }
            if (footerPos < elHeight) {
                el.classList.add('blocked');
            } else {
                el.classList.remove('blocked');
            }
        }

        function setup() {
            elHeight = el.offsetHeight;
            mainCol.style.minHeight = elHeight + 'px';
            checkSticky();
        }

        window.addEventListener('load', setup);
        window.addEventListener('resize:end', setup, false);
        document.addEventListener('scroll', checkSticky);
    })();


    // show password fields
    forEach.call(document.getElementsByClassName('show-password'), function(el) {
        var targetEls = document.querySelectorAll(el.getAttribute('data-target'));

        el.addEventListener('click', function(ev) {
            ev.preventDefault();

            var isActive = el.classList.toggle('active');

            for (var i = targetEls.length >>> 0; i--;) {
                targetEls[i].type = isActive ? 'text' : 'password';
            }
        });
    });


    forEach.call(document.getElementsByClassName('mosaic'), wzlMosaic);
    forEach.call(document.getElementsByClassName('active-label'), wzlLabels);

    forEach.call(document.getElementsByClassName('toggle'), function(el) {
        el.addEventListener('click', function(ev) {
            ev.preventDefault();
            wzlToggles(el);
        });
    });

    document.documentElement.classList.remove('no-js');
    document.documentElement.classList.add('js');
})();
