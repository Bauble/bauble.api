'use strict';

angular.module('BaubleApp')
    .controller('NotesEditorCtrl', function ($scope) {
        $scope.notes = [];
        $scope.addNote = function() {
            $scope.notes.push({});
        };
    });