"
I am a helper class that is used for locating binary file assets that are versioned along a git project repository. My subclasses implement different mechanisms for locating these binary assets. For example, in Pharo the iceberg registry is probed for the cloned location.
"
Class {
	#name : #PhaNAPIGitProjectAssetsLocator,
	#superclass : #Object,
	#category : #'PhaNAPI-GitAssets'
}

{ #category : #assets }
PhaNAPIGitProjectAssetsLocator class >> attemptToFindAssetsForThisSessionSpecifiedIn: assetsSpecClass [
	^ nil
]

{ #category : #assets }
PhaNAPIGitProjectAssetsLocator class >> findAssetsForThisSessionSpecifiedIn: assetsSpecClass [
	self allSubclassesDo: [ :sc |
		| found |
		found := sc attemptToFindAssetsForThisSessionSpecifiedIn: assetsSpecClass.
		found ifNotNil: [ ^ found ]
	].

	self error: 'Failed to find assets specified in ' , assetsSpecClass asString
]
