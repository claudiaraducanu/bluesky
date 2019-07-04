from bluesky.traffic.route import Route

def patch_route(twdefault):

    Route.twdefault = twdefault
    old_route_init = Route.__init__

    def new_route_init(self, *k, **kw):
        old_route_init(self, *k, **kw)

        self.wprta  = []        # [s] required time of arrival at way-point
        self.wptw   = []        # [s] time window size around RTA
        self.wpmode = []        # afms mode from way-point

    Route.__init__ = new_route_init

    old_route_addwpt_data = Route.addwpt_data

    def new_route_addwpt_data(self, overwrt, wpidx, *k, **kw):

        old_route_addwpt_data(self, overwrt, wpidx, *k, **kw)
        if overwrt:
            self.wprta[wpidx] = -1.                         # negative indicates no rta
            self.wptw[wpidx] = Route.twdefault # TW default size is 60
            self.wpmode[wpidx] = 1                      # Set advanced FMS mode to continue

        else:
            self.wprta.insert(wpidx, -1.)
            self.wptw.insert(wpidx, Route.twdefault)
            self.wpmode.insert(wpidx, 1)

    Route.addwpt_data = new_route_addwpt_data

    old_route_del_wpt_data = Route._del_wpt_data

    def new_del_wpt_data(self, wpidx):
        old_route_del_wpt_data(self, wpidx)
        del self.wprta[wpidx]
        del self.wptw[wpidx]
        del self.wpmode[wpidx]

    Route._del_wpt_data = new_del_wpt_data