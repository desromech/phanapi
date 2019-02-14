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
			baseline: 'NeoJSON' with: [
				spec
				repository: 'github://svenvc/NeoJSON/repository' ].

		spec 
			package: #'PhaNAPI-BinTray' with: [
				spec requires: #('NeoJSON' ). ]. ].

]
