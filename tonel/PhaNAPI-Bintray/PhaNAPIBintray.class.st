"
I provide utilities for querying and downloading shared objects and DLLs that are uploaded to bintray.
"
Class {
	#name : #PhaNAPIBintray,
	#superclass : #PhaNAPIWebBinaryRepository,
	#instVars : [
		'platformMode',
		'currentPlatformMode'
	],
	#category : #'PhaNAPI-Bintray'
}

{ #category : #'as yet unclassified' }
PhaNAPIBintray class >> fetchLibrary: libraryName fromUser: useName repository: repository package: package [
	^ self new fetchLibrary: libraryName fromUser: useName repository: repository package: package
]

{ #category : #bintray }
PhaNAPIBintray >> downloadUser: userName repository: repository package: package latestVersionForMode: mode platform: platform [
	| latestVersionFiles latestVersionFileName downloadUri downloadTarget |
	latestVersionFiles := self getUser: userName repository: repository package: package latestVersionForMode: mode platform: platform.
	latestVersionFiles ifEmpty: [ 
		self error: 'Failed to find library file.'
	].

	latestVersionFileName := latestVersionFiles first.
	downloadUri := (('https://dl.bintray.com/:user/:repository/:file_path'
		copyReplaceAll: ':user' with: userName)
		copyReplaceAll: ':repository' with: repository)
		copyReplaceAll: ':file_path' with: latestVersionFileName.
	downloadTarget := PhaNAPI uniqueInstance downloadsDirectory asFileReference / latestVersionFileName.
	downloadTarget parent ensureCreateDirectory.
	downloadTarget exists ifTrue: [ downloadTarget delete ].
	
	(self doHTTPRequest: [
		self withZincRedirectionHack: [ 
			(ZnClient new
				url: downloadUri;
				followRedirects: true;
				signalProgress: true;
				downloadTo: downloadTarget) 
		]
	] withProgress: ('Downloading {1} ...' format: {downloadTarget basename})) ifFalse: [ 
		self error: 'Failed to download the requested library.'
	].
	^ downloadTarget
]

{ #category : #bintray }
PhaNAPIBintray >> fetchLibrary: libraryName fromUser: userName repository: repository package: package [
	| archive |
	(PhaNAPI fullLibraryPathForCurrentPlatform: libraryName package: repository) ifNotNil: [
		^ self
	].
	
	archive := self downloadUser: userName repository: repository package: package latestVersionForMode: currentPlatformMode platform: Smalltalk os bintrayPlatformName.
	PhaNAPI uniqueInstance decompressLibraryArchive: archive
]

{ #category : #bintray }
PhaNAPIBintray >> getLatestVersionFileListForUser: userName repository: repository package: package [
	| versionInfo fileList |
	versionInfo := self getLatestVersionInfoForUser: userName repository: repository package: package.
	fileList := self getVersion: (versionInfo at: 'name') fileListForUser: userName repository: repository package: package.
	^ fileList collect: [ :fileInfo | fileInfo at: 'path' ]
]

{ #category : #bintray }
PhaNAPIBintray >> getLatestVersionInfoForUser: userName repository: repository package: package [
	| uri |
	uri := (('https://api.bintray.com/packages/:user/:repository/:package/versions/_latest'
		copyReplaceAll: ':user' with: userName)
		copyReplaceAll: ':repository' with: repository)
		copyReplaceAll: ':package' with: package.
	^ self requestJSON: uri
]

{ #category : #bintray }
PhaNAPIBintray >> getUser: userName repository: repository package: package latestVersionForMode: mode platform: platform [
	| fileList |
	fileList := self getLatestVersionFileListForUser: userName repository: repository package: package.
	^ fileList select: [ :path | (path includesSubstring: mode) and: (path includesSubstring: platform , '_')]
]

{ #category : #bintray }
PhaNAPIBintray >> getVersion: versionName fileListForUser: userName repository: repository package: package [
	| uri |
	uri := ((('https://api.bintray.com/packages/:user/:repository/:package/versions/:version/files'
		copyReplaceAll: ':user' with: userName)
		copyReplaceAll: ':repository' with: repository)
		copyReplaceAll: ':package' with: package)
		copyReplaceAll: ':version' with: versionName.
	^ self requestJSON: uri
]

{ #category : #initialization }
PhaNAPIBintray >> initialize [
	super initialize.
	currentPlatformMode := 'release'
	
]

{ #category : #hack }
PhaNAPIBintray >> queryKeyValueSafeSet [
	"When a query is interpreted as a list of key=value&.. pairs,
	it is better to encode = and & and leave them out of the safe set.
	Furthermore, since + is interpreted as space in the query part,
	it is unsafe as well"
	
	^ 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.~!$''()*,:@/?'
]

{ #category : #hack }
PhaNAPIBintray >> withZincRedirectionHack: aBlock [
	"See https://github.com/svenvc/zinc/issues/31"
	| oldMethod newMethod |
	self flag: 'FIXME: Remove me after this is fixed on Zinc'.
	oldMethod := ZnResourceMetaUtils class methodDict at: #queryKeyValueSafeSet.
	newMethod := self class methodDict at: #queryKeyValueSafeSet.
	[ 
		ZnResourceMetaUtils class methodDict at: #queryKeyValueSafeSet put: newMethod.
		^ aBlock value
	] ensure: [
		ZnResourceMetaUtils class methodDict at: #queryKeyValueSafeSet put: oldMethod.
	]

]
