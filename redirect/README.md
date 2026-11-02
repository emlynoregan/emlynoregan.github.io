# Root domain redirect

Owner requested on 2 November 2026: replace emlynoregan.com with a server-side
redirect to Everything's home. The old static files remain in Git for recovery.

## Deployment scope

Use legacy AWS account `214770884410`, profile `legacy-existing`, CloudFront
control plane in `us-east-1`. Identity was verified before planning. The existing
distribution `E7XLBZDR5GVHB` (`d1yyu588p4ns2m.cloudfront.net`) is disabled, already
owns the exact `emlynoregan.com` alias, and has an issued ACM certificate for it.
It is not managed by CloudFormation.

1. Create and test the `emlynoregan-root-to-everything` CloudFront Function from
   `function.js`, then publish it.
2. Associate it with viewer requests in both existing cache behaviors. Enable
   the distribution. Allow HTTP as well as HTTPS into the function so both get
   a direct redirect to the HTTPS destination. Preserve the certificate, origins,
   cache configuration, aliases and other distribution settings.
3. Wait for `Deployed`, then verify the root hostname using that distribution
   before changing DNS.
4. Replace only the apex A record in Route 53 zone `Z01363303HJW7MS0Z4BB4`
   with a CloudFront alias. Its previous TTL is 300 seconds and its four values
   are GitHub Pages addresses: `185.199.108.153`, `185.199.109.153`,
   `185.199.110.153`, `185.199.111.153`.
5. Verify authoritative DNS and real HTTP/HTTPS 301 responses.

All old paths and queries redirect to the fixed Everything home URL. They are
not appended to the destination. Browser redirect caching is limited to five
minutes. The bare `www` hostname currently has no DNS record and is outside
this change. Other subdomains, including Everything and its MCP, remain on
their existing distributions and records.

There is no new server, certificate, bucket, Lambda, paid subscription or
scheduled job. One request-priced CloudFront Function is added; redirects are
returned at the edge before an origin fetch. No content is deleted.

## Run and recover

`deploy.py` uses boto3 from the existing local deployment environment. State and
full preimages live outside this repository, in the task's dated
`root-redirect-20261102/` folder. Its explicit commands are `edge`, `status`,
`dns` and `rollback-dns`; there is no automatic apply, write retry or waiter.
The edge command requires exact equality with the inspected distribution
preimage. DNS cutover requires successful direct-hostname proofs, a deployed
distribution and the unchanged old A record. Stop and inspect the journal after
an interrupted mutation rather than replaying it.

Restore the saved GitHub A record with `rollback-dns` to return traffic to the
unchanged GitHub Pages site. After DNS has propagated, restore the saved
distribution config with a fresh CloudFront ETag if the edge change also needs
reversal. Do not delete the function while it is associated. No rollback
requires deleting any website files.

Reference: [AWS CloudFront Functions redirect tutorial](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/functions-tutorial.html).
