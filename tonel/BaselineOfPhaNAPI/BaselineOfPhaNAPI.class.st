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
		spec 
			package: #'PhaNAPI-Core' with: [].
		spec 
			package: #'PhaNAPI-GitAssets' with: [
				spec requires: #(#'PhaNAPI-Core'). ].
    ].

	spec for: #pharo do: [
		spec 
			package: #'PhaNAPI-Bintray' with: [
				spec requires: #(#'PhaNAPI-Core'). ].
		spec 
			package: #'PhaNAPI-GitHubRelease' with: [
				spec requires: #(#'PhaNAPI-Core'). ].
		spec 
			package: #'PhaNAPI-Iceberg' with: [
				spec requires: #(#'PhaNAPI-Core' #'PhaNAPI-GitHubRelease' #'PhaNAPI-GitAssets'). ].
    ].

	spec for: #squeak do: [
		spec 
			package: #'PhaNAPI-Squeak' with: [
				spec requires: #(#'PhaNAPI-Core'). ].
    ].

]
