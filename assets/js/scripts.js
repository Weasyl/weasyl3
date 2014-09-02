'use strict';

var forEach = Array.prototype.forEach;

if (!document.documentElement.classList && Object.defineProperty && typeof HTMLElement !== 'undefined') {
    var DOMTokenList = function DOMTokenList() {
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
        }).join(" ");
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


// helper functions: replace jquery parents() method
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


// weasyl mosaic thumbnail layout
// https://www.weasyl.com/~aden
function wzlMosaic(el) {
    var maxBlockWidth = 96,
        aspectRatios = [0.33, 0.66, 1, 1.5, 3],
        appendEls = el.getElementsByClassName('mosaic-append'),
        grid = [],
        tiles, tileCount, containerWidth, blockDim, columnCount, globalOffset;

    el.classList.add('enabled');

    // create a new grid row of empty cells at specified y position
    function newGridRow(row) {
        grid[row] = [];
        for ( var i = 0; i < columnCount; i++ ) {
            grid[row].push(0);
        }
    }

    // set up container properties
    function setupContainer() {
        globalOffset = 0;
        containerWidth = el.offsetWidth;
        columnCount = Math.ceil(containerWidth / maxBlockWidth);
        blockDim = Math.floor(containerWidth / columnCount);

        // wipe existing grid (if any) and create three empy grid rows to work within
        grid.length = 0;
        newGridRow(0); newGridRow(1); newGridRow(2);

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
        }
    }

    // process tile properties
    function setupTiles(offset) {
        if ( !offset ) { offset = 0; }
        tiles = toArray(el.getElementsByClassName('item'));
        tileCount = tiles.length;

        var offsetTiles = tiles.slice(offset);
        for ( var i = 0; i < offsetTiles.length; i++ ) {
            var thisTile = offsetTiles[i],
                aspectRatio = parseFloat(thisTile.getAttribute('data-init-aspect')),
                closestRatio = null,
                thumbImage = thisTile.querySelector('.thumb').getAttribute('src'),
                childA = thisTile.querySelector('a');

            // set as background image in order to let the browser handle sizing
            childA.style.backgroundImage = 'url("' + thumbImage + '")';

            // assign closest aspect
            for ( var j = 0; j < aspectRatios.length; j++ ) {
                if (closestRatio === null || Math.abs(aspectRatios[j] - aspectRatio) < Math.abs(closestRatio - aspectRatio)) {
                    closestRatio = aspectRatios[j];
                }
            }
            thisTile.setAttribute('data-snapped-aspect', closestRatio);
            thisTile.setAttribute('data-placed', 0);

            // assign cell dimensions and denote resizeability
            if (closestRatio == 0.33) {
                thisTile.setAttribute('data-sizeX', 1);
                thisTile.setAttribute('data-sizeY', 3);
                thisTile.setAttribute('data-resizeable2', 0);
                thisTile.setAttribute('data-resizeable1', 0);
            } else if (closestRatio == 0.66) {
                thisTile.setAttribute('data-sizeX', 2);
                thisTile.setAttribute('data-sizeY', 3);
                thisTile.setAttribute('data-resizeable2', 0);
                thisTile.setAttribute('data-resizeable1', 1);
                thisTile.setAttribute('data-size1X', 1);
                thisTile.setAttribute('data-size1Y', 2);
            } else if (closestRatio == 1) {
                thisTile.setAttribute('data-sizeX', 3);
                thisTile.setAttribute('data-sizeY', 3);
                thisTile.setAttribute('data-resizeable2', 1);
                thisTile.setAttribute('data-size2X', 2);
                thisTile.setAttribute('data-size2Y', 2);
                thisTile.setAttribute('data-resizeable1', 1);
                thisTile.setAttribute('data-size1X', 1);
                thisTile.setAttribute('data-size1Y', 1);
            } else if (closestRatio == 1.5) {
                thisTile.setAttribute('data-sizeX', 3);
                thisTile.setAttribute('data-sizeY', 2);
                thisTile.setAttribute('data-resizeable2', 1);
                thisTile.setAttribute('data-size2X', 2);
                thisTile.setAttribute('data-size2Y', 1);
                thisTile.setAttribute('data-resizeable1', 0);
            } else if (closestRatio == 3) {
                thisTile.setAttribute('data-sizeX', 3);
                thisTile.setAttribute('data-sizeY', 1);
                thisTile.setAttribute('data-resizeable2', 0);
                thisTile.setAttribute('data-resizeable1', 0);
            }
        }
    }

    // the fun part
    function mosaicLayout(isAppend) {
        var curTile = 0,
            isLookahead = false,
            posX = 0,
            posY = 0;

        // if appending to existing data, find starting row
        if (isAppend) {
            for ( var i = grid.length - 1; i >= 0; i-- ) {
                if ( grid[i].indexOf(0) > -1) {
                    posY = i;
                } else {
                    break;
                }
            }
        }

        // function to find empty spaces to the right of a given point
        function findSpaceFromPoint(posX, posY) {
            if (posX >= columnCount) { return [false, posX]; }
            var availableSpace = 0;

            while ( grid[posY][posX] == 1 ) {
                if (posX >= columnCount) { return [false, posX]; }
                posX++;
            }
            var shiftedX = posX;

            while (posX < columnCount) {
                availableSpace++;
                posX++;
                if ( grid[posY][posX] == 1 ) { break; }
            }

            return [availableSpace, shiftedX];
        }

        // function to place a tile into the grid
        function placeTile(t) {
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
            if (curTile >= tileCount) { break; }

            var thisTile = tiles[curTile],
                tileSizeX = parseInt(thisTile.getAttribute('data-sizeX')),
                tileSizeY = parseInt(thisTile.getAttribute('data-sizeY'));

            // get space available right now
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
                // alert('found space');
                placeTile(curTile);
            } else if ( spaceAvail[0] >= 2 && thisTile.getAttribute('data-resizeable2') == 1 ) {
                // alert('shrunk to 2');
                tileSizeX = parseInt(thisTile.getAttribute('data-size2X'));
                tileSizeY = parseInt(thisTile.getAttribute('data-size2Y'));
                thisTile.setAttribute('data-sizeX', tileSizeX);
                thisTile.setAttribute('data-sizeY', tileSizeY);
                placeTile(curTile);
            } else if ( spaceAvail[0] >= 1 && thisTile.getAttribute('data-resizeable1') == 1 ) {
                // alert('shrunk to 1');
                tileSizeX = parseInt(thisTile.getAttribute('data-size1X'));
                tileSizeY = parseInt(thisTile.getAttribute('data-size1Y'));
                thisTile.setAttribute('data-sizeX', tileSizeX);
                thisTile.setAttribute('data-sizeY', tileSizeY);
                placeTile(curTile);
            } else {
                // alert("didn't find space");
                var b = 0;
                var foundTile = false;
                for ( b = curTile + 1; b < tileCount; b++ ) {
                    if ( tiles[b].getAttribute('data-placed') < 1 ) {
                        foundTile = true;
                        break;
                    }
                }
                if (foundTile) {
                    // alert('looking ahead');
                    foundTile = false;
                    isLookahead = true;
                    curTile = b;
                    continue;
                }
                // if didn't find a suitable tile, do what we can with remaining space
                if (posX < columnCount) {
                    // alert('advancing x position, trying again');
                    posX++;
                    continue;
                } else {
                    // alert('making new row, trying again');
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
        if (!offset) { offset = 0; }

        for ( var i = offset; i < tileCount; i++ ) {
            var thisTile = tiles[i],
                thisInfo = thisTile.querySelector('.info'),
                thisWidth = parseInt(thisTile.getAttribute('data-sizeX')) * blockDim,
                thisHeight = parseInt(thisTile.getAttribute('data-sizeY')) * blockDim,
                thisPosX = parseInt(thisTile.getAttribute('data-tilePosX')) * blockDim,
                thisPosY = parseInt(thisTile.getAttribute('data-tilePosY')) * blockDim;

            thisTile.style.width = thisWidth + 'px';
            thisTile.style.height = thisHeight + 'px';
            thisTile.style.left = thisPosX + 'px';
            thisTile.style.top = thisPosY + 'px';

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

            globalOffset++;
        }

        // trim grid
        var trimLength = 0;
        for (var n = grid.length - 1; n >= 0; n--) {
            if (grid[n].indexOf(1) <= -1) {
                trimLength++;
            } else {
                break;
            }
        }
        // and set height of container
        el.style.height = ((grid.length - trimLength) * blockDim) + 'px';

        // log
        // var logEl = document.getElementById('log');
        // for (var k = 0; k < grid.length; k++) {
        //     logEl.innerHTML = logEl.innerHTML + grid[k] + '<br />';
        // }
    }

    // light the fuse
    setupContainer();
    setupTiles();
    mosaicLayout();
    drawTiles();

    // recalculate on resize
    window.addEventListener('resize:end', function(event) {
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
    el.addEventListener('mouseleave', function() {
        hoverDebounce = false;
        clearTimeout(hoverDelay);
        el.classList.remove('hovered');
    });
}


// generic toggles
// <el class="toggle" data-toggle-target="[next|parentnext|css-selector]" />
function wzlToggles(el) {
    var toggleTarget = el.getAttribute('data-toggle-target'),
        targetObject = null;

    if ( toggleTarget == 'next' ) {
        targetObject = el.nextElementSibling;
    } else if ( toggleTarget == 'parentnext' ) {
        targetObject = el.parentNode.nextElementSibling;
    } else if ( toggleTarget == 'parentparentnext' ) {
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
}


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

    input.addEventListener('focus', function() {
        el.classList.add('active');
    });
    input.addEventListener('blur', function() {
        el.classList.remove('active');
        checkFilled();
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
        window.dispatchEvent(event);
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

forEach.call(document.getElementsByClassName('mosaic'), wzlMosaic);
forEach.call(document.getElementsByClassName('active-label'), wzlLabels);

forEach.call(document.getElementsByClassName('toggle'), function(el) {
    el.addEventListener('click', function(ev) {
        ev.preventDefault();
        wzlToggles(el);
    });
});


// slightly refine header search hover
(function() {
    var el = document.querySelector('.header-search-input');
    el.addEventListener('focus', function() {
        el.parentNode.classList.add('active');
    });
    el.addEventListener('blur', function() {
        el.parentNode.classList.remove('active');
    });
})();


// art zoom
(function() {
    var el = document.querySelector('.sub-zoom-toggle');

    if ( el ) {
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
    }
})();


// modal escape listener
(function() {
    var modals = document.getElementsByClassName('modal');
    if ( modals.length > 0 ) {
        window.addEventListener('keydown', function(ev) {
            if ( ev.keyCode == 27 ) {
                for ( var i=0; i < modals.length; i++ ) {
                    modals[i].classList.remove('active');
                }
            }
        });
    }
})();


// checkbox/radio classes
(function() {
    var inputs = document.querySelectorAll('input[type=checkbox], input[type=radio]');
    forEach.call(inputs, function(el) {
        var parentLabel = getParentsByTagName(el, 'label')[0],
            isParent = el.classList.contains('checkbox-parent'),
            isChild = el.classList.contains('checkbox-child');

        if ( el.checked ) {
            parentLabel.classList.add('checked');
        }

        el.addEventListener('change', function() {
            if ( isParent || isChild ) {
                // dependent checkboxes
                var groupEl = getParentsByClassName(el, 'checkbox-group')[0],
                    parentBox = groupEl.getElementsByClassName('checkbox-parent')[0],
                    childBoxes = groupEl.getElementsByClassName('checkbox-child');
                if ( isParent ) {
                    forEach.call(childBoxes, function(childEl) {
                        childEl.checked = el.checked;
                    });
                } else if ( !el.checked ) {
                    parentBox.checked = false;
                }

                var allBoxes = [parentBox];
                Array.prototype.push.apply(allBoxes, childBoxes);

                allBoxes.forEach(function(thisBox) {
                    var thisLabel = getParentsByTagName(thisBox, 'label')[0];

                    thisLabel.classList.toggle('checked', thisBox.checked);
                });
            } else {
                // normal single behavior
                parentLabel.classList.toggle('checked');
            }
        });
    });
})();


// sticky notif utility scroll
function getTopOffset(el) {
    var y = 0;
    while ( el ) {
        y += (el.offsetTop - el.scrollTop + el.clientTop);
        el = el.offsetParent;
    }
    return y;
}
(function() {
    var el = document.querySelector('.sticky-top'),
        container = document.querySelector('.col-main'),
        elPos = getTopOffset(el),
        elHeight, scrollPos, footerPos;

    if (!el) {
        return;
    }

    function setup() {
        elHeight = el.offsetHeight;
        container.style.minHeight = elHeight + 'px';
        footerPos = getTopOffset(document.getElementsByClassName('page-footer')[0]);
    }

    window.addEventListener('load', setup);
    window.addEventListener('resize:end', setup, false);

    document.addEventListener('scroll', function() {
        scrollPos = window.pageYOffset;
        if ( scrollPos > elPos ) {
            el.classList.add('stuck');
        } else {
            el.classList.remove('stuck');
        }
        if ( scrollPos > (footerPos - elHeight) ) {
            el.classList.add('blocked');
        } else {
            el.classList.remove('blocked');
        }
    });
})();

document.documentElement.classList.remove('no-js');
document.documentElement.classList.add('js');
