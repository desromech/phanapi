"
I provide utilities for querying and downloading shared objects and DLLs that are uploaded to GitHub Releases.
"
Class {
	#name : #PhaNAPIGitHubRelease,
	#superclass : #PhaNAPIWebBinaryRepository,
	#instVars : [
		'platformMode',
		'currentPlatformMode'
	],
	#category : #'PhaNAPI-GitHubRelease'
}

{ #category : #'as yet unclassified' }
PhaNAPIGitHubRelease class >> fetchLibrary: libraryName fromUser: userName repository: repository [
	^ self new fetchLibrary: libraryName fromUser: userName repository: repository release: nil
]

{ #category : #'as yet unclassified' }
PhaNAPIGitHubRelease class >> fetchLibrary: libraryName fromUser: userName repository: repository release: releaseName [
	^ self new fetchLibrary: libraryName fromUser: userName repository: repository release: releaseName
]

{ #category : #private }
PhaNAPIGitHubRelease >> downloadAssetNamed: downloadFileName uri: downloadFileURI [
	| downloadTarget |
	downloadTarget := PhaNAPI uniqueInstance downloadsDirectory asFileReference / downloadFileName.
	downloadTarget parent ensureCreateDirectory.
	downloadTarget exists ifTrue: [ downloadTarget delete ].

	ZnOptions globalDefault clone
		at: #queryKeyValueSafeSet put: (ZnOptions queryKeyValueSafeSet \ '/;');
		during: [
			(self doHTTPRequest: [
			(ZnClient new
				"If we do not set the accept header, we might get a JSON describing the asset."
				accept: 'application/octet-stream';
				url: downloadFileURI;
				followRedirects: true;
				signalProgress: true;
				downloadTo: downloadTarget) 
		] withProgress: ('Downloading {1} ...' format: {downloadTarget basename})) ifFalse: [ 
			self error: 'Failed to download the requested library.'
		].
	].

	^ downloadTarget
]

{ #category : #private }
PhaNAPIGitHubRelease >> downloadUser: userName repository: repository release: releaseName forMode: mode platform: platform [
	| latestVersionFiles downloadFile |
	latestVersionFiles := self getUser: userName repository: repository release: releaseName forMode: mode platform: platform.
	latestVersionFiles ifEmpty: [ 
		self error: 'Failed to find library file.'
	].

	downloadFile := latestVersionFiles first.
	^ self downloadAssetNamed: downloadFile key uri: downloadFile value
]

{ #category : #private }
PhaNAPIGitHubRelease >> extractFiles: fileList forMode: mode platform: platform [
	^ fileList select: [ :keyValue |
		| name |
		name := keyValue key.
		(name includesSubstring: mode) and: (name includesSubstring: platform , '_')
	]
]

{ #category : #API }
PhaNAPIGitHubRelease >> fetchLibrary: libraryName fromUser: userName repository: repository release: releaseName [
	| archive |
	(PhaNAPI fullLibraryPathForCurrentPlatform: libraryName package: repository) ifNotNil: [
		^ self
	].

	archive := self downloadUser: userName repository: repository release: releaseName forMode: currentPlatformMode platform: Smalltalk os phanapiPlatformName.
	PhaNAPI uniqueInstance decompressLibraryArchive: archive
]

{ #category : #private }
PhaNAPIGitHubRelease >> getFileListFromVersion: releaseVersionInfo [
	^ (releaseVersionInfo at: 'assets' ifAbsent: [#()]) collect: [ :asset |
		(asset at: 'name') -> (asset at: 'url')
	]
]

{ #category : #private }
PhaNAPIGitHubRelease >> getLatestVersionForUser: userName repository: repository [
	| uri |
	uri := ('https://api.github.com/repos/:user/:repository/releases/latest'
		copyReplaceAll: ':user' with: userName)
		copyReplaceAll: ':repository' with: repository.
	^ self requestJSON: uri
]

{ #category : #private }
PhaNAPIGitHubRelease >> getRelease: releaseName fileListForUser: userName repository: repository [
	^ self getFileListFromVersion: (self getRelease: releaseName versionForUser: userName repository: repository)
]

{ #category : #private }
PhaNAPIGitHubRelease >> getRelease: releaseName versionForUser: userName repository: repository [
	| uri |
	uri := releaseName ifNotNil: [ 
		(('https://api.github.com/repos/:user/:repository/releases/tags/:tagName'
			copyReplaceAll: ':user' with: userName)
			copyReplaceAll: ':repository' with: repository)
			copyReplaceAll: ':tagName' with: releaseName
	] ifNil: [ 
		('https://api.github.com/repos/:user/:repository/releases/latest'
			copyReplaceAll: ':user' with: userName)
			copyReplaceAll: ':repository' with: repository
	].
	^ self requestJSON: uri
]

{ #category : #private }
PhaNAPIGitHubRelease >> getUser: userName repository: repository release: releaseName forMode: mode platform: platform [
	| fileList |
	fileList := self getRelease: releaseName fileListForUser: userName repository: repository.
	^ self extractFiles: fileList forMode: mode platform: platform
]

{ #category : #initialization }
PhaNAPIGitHubRelease >> initialize [
	super initialize.
	currentPlatformMode := 'release'
]
