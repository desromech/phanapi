"
I provide the required glue for connecting a library that can be downloaded with PhaNAPI with the uFFI.
"
Class {
	#name : #PhaNAPILibrary,
	#superclass : #FFILibrary,
	#instVars : [
		'librarySearchSession',
		'libraryFullNameForThisSession'
	],
	#category : #'PhaNAPI-Core-LibrarySolving'
}

{ #category : #'library downloading' }
PhaNAPILibrary >> fetchLibrary [
	"This method takes care of fetching the actual library. For example, if the
	library is built using CI, and deployed into bintray, it could be fetched with
	the following example:
	
	PhaNAPIBintray fetchLibrary: 'Agpu' fromUser: 'ronsaldo' repository: 'abstract-gpu' package: 'lib'.
	
	This method can also be called in a package post load action.
	"
	
	self subclassResponsibility
]

{ #category : #'library path' }
PhaNAPILibrary >> ffiLibraryName [
	librarySearchSession ~~ Smalltalk session ifTrue: [ 
		self findLibraryPath ifNotNil: [ :path |
			libraryFullNameForThisSession := path fullName
		] ifNil: [ 
			self fetchLibrary.
			self findLibraryPath ifNotNil: [ :path |
				libraryFullNameForThisSession := path fullName
			] ifNil: [
				self error: 'Failed to find the downloaded library.'
			]
		].
		
		librarySearchSession := Smalltalk session
	].

	^ libraryFullNameForThisSession
]

{ #category : #'library path' }
PhaNAPILibrary >> findLibraryPath [
	"This method should attempt to find the actual library path. For example,
	 it could be implemented in the following way:
	^ PhaNAPI fullLibraryPathForCurrentPlatform: 'Agpu' package: 'abstract-gpu'
	"
	^ self subclassResponsibility
]

{ #category : #'accessing platform' }
PhaNAPILibrary >> macModuleName [ 
	^ self shouldNotImplement
]

{ #category : #'accessing platform' }
PhaNAPILibrary >> unixModuleName [
	^ self shouldNotImplement
]

{ #category : #'accessing platform' }
PhaNAPILibrary >> win32ModuleName [ 
	^ self shouldNotImplement
]
