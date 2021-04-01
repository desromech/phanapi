"
I am an utility class used for finding the filesystem location of a cloned iceberg repository that corresponds to a specific class.

I am to be used to facilitate storing data assets in git repositories.
"
Class {
	#name : #PhaNAPIIcebergProjectAssets,
	#superclass : #Object,
	#classInstVars : [
		'session',
		'location'
	],
	#category : #'PhaNAPI-Iceberg'
}

{ #category : #hooks }
PhaNAPIIcebergProjectAssets class >> adjustLocation: repoLocation [
	^ repoLocation
]

{ #category : #defaults }
PhaNAPIIcebergProjectAssets class >> fallbackLocation [
	^ Smalltalk imageDirectory asFileReference asAbsolute canonicalize
]

{ #category : #private }
PhaNAPIIcebergProjectAssets class >> findAssets [
	| packageName |
	packageName := self package name.
	IceRepository registry
		detect: [ :each | each includesPackageNamed: packageName ]
		ifFound: [ :found | ^ self adjustLocation: found location asFileReference asAbsolute canonicalize ].

	^ self adjustLocation: self fallbackLocation
]

{ #category : #accessing }
PhaNAPIIcebergProjectAssets class >> location [
	session ~~ Smalltalk session ifTrue: [ 
		location := self findAssets.
		session := Smalltalk session
	].
	^ location
]
