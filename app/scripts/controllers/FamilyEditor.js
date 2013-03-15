'use strict';

angular.module('BaubleApp')
    .controller('FamilyEditorCtrl', function ($scope, Family) {
        $scope.family = {};
        $scope.Family = Family;

        // get the family details when the selection is changed
        if($scope.selected) {
            $scope.$watch('selected', function() {
                $scope.Family.details($scope.selected, function(result) {
                    $scope.family = result.data;
                });
            });
        }

        $scope.activeTab = "general";
        $scope.qualifiers = ["s. lat.", "s. str."];

        $scope.selectOptions = {
            minimumInputLength: 1,

            formatResult: function(object, container, query) { return object.str; },
            formatSelection: function(object, container) { return object.str; },

            id: function(obj) {
                return obj.ref; // use ref field for id since our resources don't have ids
            },

            // get the list of families matching the query
            query: function(options){
                // TODO: somehow we need to cache the returned results and early search
                // for new results when the query string is something like .length==2
                // console.log('query: ', options);....i think this is what the
                // options.context is for
                Family.query(options.term + '%', function(response){
                    $scope.families = response.data.results;
                    if(response.data.results && response.data.results.length > 0)
                        options.callback({results: response.data.results});
                });
            }
        };

        $scope.addSynonym = function(synonym) {
            if(!$scope.family.synonyms) {
                $scope.family.synonyms = [synonym];
            } else {
                $scope.family.synonyms.push(synonym);
            }
        };

        $scope.close = function() {
            $scope.showEditor = false;
        }

        $scope.save = function() {
            // TODO: we need a way to determine if this is a save on a new or existing
            // object an whether we whould be calling save or edit

            // TODO: we could probably also update the selected result to reflect
            // any changes in the search result
            $scope.family = $scope.Family.save($scope.family);
            $scope.close();
        };

    });
