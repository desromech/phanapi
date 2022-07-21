"
I am an utility class used for finding the filesystem location of a cloned iceberg repository that corresponds to a specific class.

I am to be used to facilitate storing data assets in git repositories.
"
Class {
	#name : #PhaNAPIIcebergProjectAssetsLocator,
	#superclass : #PhaNAPIGitProjectAssetsLocator,
	#category : #'PhaNAPI-Iceberg'
}

{ #category : #assets }
PhaNAPIIcebergProjectAssetsLocator class >> attemptToFindAssetsForThisSessionSpecifiedIn: assetsSpecClass [
	| packageName |
	packageName := assetsSpecClass package name.
	IceRepository registry
		detect: [ :each | each includesPackageNamed: packageName ]
		ifFound: [ :found | ^ assetsSpecClass adjustLocation: found location asFileReference asAbsolute canonicalize ].

	^ assetsSpecClass adjustLocation: self fallbackLocation
]

{ #category : #defaults }
PhaNAPIIcebergProjectAssetsLocator class >> fallbackLocation [
	^ Smalltalk imageDirectory asFileReference asAbsolute canonicalize
]

{ #category : #private }
PhaNAPIIcebergProjectAssetsLocator class >> findAssets [
	| packageName |
	packageName := self package name.
	IceRepository registry
		detect: [ :each | each includesPackageNamed: packageName ]
		ifFound: [ :found | ^ self adjustLocation: found location asFileReference asAbsolute canonicalize ].

	^ self adjustLocation: self fallbackLocation
]
