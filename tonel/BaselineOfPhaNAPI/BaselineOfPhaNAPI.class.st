Class {
	#name : #BaselineOfPhaNAPI,
	#superclass : #BaselineOf,
	#category : #BaselineOfPhaNAPI
}

{ #category : #baselines }
BaselineOfPhaNAPI >> baseline: spec [
	<baseline>
	spec for: #'common' do: [
		spec blessing: #'baseline'.
		spec baseline: #'NeoJSON' with: [ spec repository: 'github://svenvc/NeoJSON/repository' ].
		"spec baseline: #'ZincHTTPComponents' with: [ spec repository: 'github://svenvc/zinc/repository' ]."

		spec 
			package: #'PhaNAPI-Core' with: [
				spec requires: #(#'NeoJSON' ). ].
		spec 
			package: #'PhaNAPI-Bintray' with: [
				spec requires: #(#'PhaNAPI-Core'). ].
		spec 
			package: #'PhaNAPI-GitHubRelease' with: [
				spec requires: #(#'PhaNAPI-Core'). ].
		spec 
			package: #'PhaNAPI-Iceberg' with: [
				spec requires: #(#'PhaNAPI-Core' #'PhaNAPI-GitHubRelease'). ].
    ].

]
